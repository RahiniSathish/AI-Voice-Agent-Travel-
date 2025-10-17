"""
API Endpoints for AI Travel Agent
FastAPI application with all REST endpoints
UNIFIED BACKEND: Azure + LiveKit Token Generation
"""

import os
import sqlite3
import uuid
import tempfile
import base64
import logging
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

# Import from local modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import DB_PATH, SERVICE_PRICES
from models import VoiceRequest, CustomerLogin, CustomerRegister, TravelBookingRequest
from utils import hash_password, verify_password, get_flight_class_options, send_booking_confirmation_email, send_password_reset_email

# Configure logging FIRST (before any other imports that use logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
# Load .env from voice/ directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
logger.info(f"📁 Loading .env from: {env_path}")
logger.info(f"📁 .env exists: {os.path.exists(env_path)}")

# LiveKit imports
try:
    from livekit.api import AccessToken, VideoGrants
    LIVEKIT_AVAILABLE = True
    logger.info("✅ LiveKit SDK loaded successfully")
except ImportError as e:
    LIVEKIT_AVAILABLE = False
    logger.warning(f"⚠️ LiveKit SDK not available: {str(e)}")

# Optional LLM imports (for when Azure credentials are not available)
try:
    from llm import get_ai_response, speech_to_text, text_to_speech, detect_language, clear_conversation_history
    LLM_AVAILABLE = True
    logger.info("✅ LLM services loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ LLM services not available: {str(e)}")
    LLM_AVAILABLE = False
    # Create dummy functions for when LLM is not available
    def get_ai_response(*args, **kwargs):
        return {"error": "LLM services not available - Azure credentials required"}
    def speech_to_text(*args, **kwargs):
        return {"error": "Speech services not available - Azure credentials required"}
    def text_to_speech(*args, **kwargs):
        return {"error": "Speech services not available - Azure credentials required"}
    def detect_language(*args, **kwargs):
        return "en"
    def clear_conversation_history(*args, **kwargs):
        return {"success": True}
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Database'))
from database import (
    get_or_create_customer,
    create_travel_booking,
    get_customer_bookings,
    save_conversation,
    get_conversation_history,
    cancel_booking,
    reschedule_booking,
    record_livekit_session,
    get_livekit_session,
    update_livekit_session_activity,
    get_livekit_transcript
)

# Initialize FastAPI
app = FastAPI(title="Travel AI Voice Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for LiveKit frontend
livekit_frontend_path = os.path.join(os.path.dirname(__file__), "../livekit_agent/frontend")
if os.path.exists(livekit_frontend_path):
    app.mount("/livekit/static", StaticFiles(directory=livekit_frontend_path), name="livekit_static")

# ==================== HEALTH CHECK ====================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "✈️ Travel AI Voice Agent with Booking",
        "status": "online",
        "voice": "Azure Speech Services",
        "features": ["Voice Chat", "Customer Login", "Travel Booking", "Multilingual"]
    }

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.get("/check_customer/{email}")
def check_customer_exists(email: str):
    """Check if a customer exists in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, name FROM customers WHERE email = ?", (email,))
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            logger.info(f"✅ Customer exists: {email}")
            return {
                "exists": True,
                "email": customer[1],
                "name": customer[2]
            }
        else:
            logger.info(f"❌ Customer not found: {email}")
            return {"exists": False}
    except Exception as e:
        logger.error(f"❌ Error checking customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
def register_customer(customer: CustomerRegister):
    """Customer registration with password"""
    try:
        # Check if customer already exists
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM customers WHERE email = ?", (customer.email,))
        existing_customer = cursor.fetchone()
        
        if existing_customer:
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        salt, password_hash = hash_password(customer.password)
        
        # Create new customer with hashed password
        cursor.execute("""
            INSERT INTO customers (email, name, password_salt, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (customer.email, customer.name, salt, password_hash, datetime.now()))
        
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        
        logger.info(f"👤 New customer registered: {customer.email}")
        return {
            "success": True,
            "customer": {
                "id": customer_id,
                "email": customer.email,
                "name": customer.name,
                "created_at": datetime.now().isoformat()
            },
            "message": "Registration successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login_customer(customer: CustomerLogin):
    """Customer login with password verification"""
    try:
        logger.info(f"🔐 LOGIN ATTEMPT: Email={customer.email}, Password length={len(customer.password)}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get customer with password hash
        cursor.execute("""
            SELECT id, email, name, password_salt, password_hash, created_at
            FROM customers WHERE email = ?
        """, (customer.email,))
        
        customer_data = cursor.fetchone()
        logger.info(f"🔐 Database query result: {customer_data}")
        
        if not customer_data:
            conn.close()
            logger.warning(f"❌ User not found: {customer.email}")
            raise HTTPException(status_code=404, detail="User not found")
        
        customer_id, email, name, salt, stored_hash, created_at = customer_data
        logger.info(f"🔐 User data: ID={customer_id}, Salt={'Yes' if salt else 'No'}, Hash={'Yes' if stored_hash else 'No'}")
        
        # Check if user has password hash (from new system)
        if not salt or not stored_hash:
            conn.close()
            logger.warning(f"❌ Login attempt failed for {customer.email}: User exists but has no password set")
            raise HTTPException(status_code=401, detail="Password not set. Please register again with a password.")
        
        # Verify password
        password_valid = verify_password(customer.password, salt, stored_hash)
        logger.info(f"🔐 Password verification result: {password_valid}")
        
        if not password_valid:
            conn.close()
            logger.warning(f"❌ Login attempt failed for {customer.email}: Incorrect password provided")
            raise HTTPException(status_code=401, detail="Incorrect password. Please check your password and try again.")
        
        conn.close()
        
        logger.info(f"👤 Customer logged in: {customer.email}")
        return {
            "success": True,
            "customer": {
                "id": customer_id,
                "email": email,
                "name": name,
                "created_at": created_at
            },
            "message": "Login successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VOICE & CHAT ENDPOINTS ====================

@app.post("/voice_chat")
async def voice_chat(request: VoiceRequest):
    """Process voice input and return AI response with audio"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        user_message = request.text
        
        logger.info(f"💬 Customer: {user_message[:50]}...")
        
        # Get AI response
        ai_message = get_ai_response(session_id, user_message)
        logger.info(f"🤖 Alex: {ai_message[:50]}...")
        
        # Detect language from user message
        detected_lang = detect_language(user_message)
        lang_code = f"{detected_lang}-IN" if detected_lang != 'en' else "en-US"
        
        logger.info(f"🌍 Responding in language: {lang_code}")
        
        # Save conversation to database if customer is logged in
        if request.customer_email:
            try:
                save_conversation(request.customer_email, session_id, "user", user_message, lang_code)
                save_conversation(request.customer_email, session_id, "assistant", ai_message, lang_code)
                logger.info(f"💾 Conversation saved for {request.customer_email}")
            except Exception as db_err:
                logger.warning(f"⚠️ Failed to save conversation: {db_err}")
        
        # Convert response to speech in detected language
        audio_data = None
        try:
            audio_bytes = text_to_speech(ai_message, lang_code)
            if audio_bytes:
                audio_data = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as audio_err:
            logger.warning(f"⚠️ TTS failed: {audio_err}")
        
        return {
            "response": ai_message,
            "audio_base64": audio_data,
            "session_id": session_id,
            "response_text": ai_message
        }
        
    except Exception as e:
        logger.error(f"❌ Error in voice_chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio to text using Azure Speech Services"""
    logger.info(f"🎤 ========== TRANSCRIBE REQUEST RECEIVED ==========")
    logger.info(f"   File: {file.filename}, Content-Type: {file.content_type}")
    
    try:
        # Save uploaded file temporarily
        temp_dir = "temp_audio_files"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(
            temp_dir, 
            f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        )
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            if not content:
                logger.error("❌ Empty audio file received!")
                raise ValueError("Empty audio file")
            buffer.write(content)
        
        file_size = os.path.getsize(temp_file_path)
        logger.info(f"✅ Audio saved: {file_size} bytes")
        
        # Transcribe using Azure Speech Services
        logger.info("🔄 Starting Azure Speech transcription...")
        transcribed_text, detected_lang = speech_to_text(temp_file_path)
        
        # Clean up
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        if not transcribed_text:
            logger.warning("⚠️ No transcription result")
            return {"error": "Could not transcribe audio", "text": "", "detected_language": "en-US", "status": "failed"}
        
        logger.info(f"✅ Transcribed: '{transcribed_text}' (Language: {detected_lang})")
        
        return {
            "text": transcribed_text,
            "detected_language": detected_lang or "en-US",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {type(e).__name__} - {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e), "text": "", "status": "failed"}

@app.get("/welcome")
def get_welcome_message():
    """Get welcome greeting with audio"""
    try:
        # Shorter, more concise welcome message for better TTS
        welcome_text = "Hello! Welcome to Attar Travel. I'm Alex, your AI travel agent for Saudi Arabia. I can help you book flights, hotels, and plan your perfect trip to destinations like Riyadh, Jeddah, and Al-Ula. How may I help you today?"
        
        # Generate audio
        audio_data = None
        try:
            logger.info(f"🎙️ Generating welcome audio ({len(welcome_text)} characters)...")
            audio_bytes = text_to_speech(welcome_text)
            if audio_bytes:
                audio_data = base64.b64encode(audio_bytes).decode("utf-8")
                logger.info(f"✅ Welcome audio generated: {len(audio_data)} bytes (base64)")
            else:
                logger.warning("⚠️ No audio bytes returned from TTS")
        except Exception as e:
            logger.error(f"⚠️ Welcome TTS failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return {
            "message": welcome_text,
            "audio_base64": audio_data
        }
    except Exception as e:
        logger.error(f"❌ Welcome error: {str(e)}")
        return {"message": "Welcome to Attar Travel - Your Saudi Arabia Travel Specialist!", "audio_base64": None}

@app.post("/clear_session")
def clear_session(session_id: str):
    """Clear conversation history for a session"""
    if clear_conversation_history(session_id):
        return {"message": "Session cleared"}
    return {"message": "Session not found"}

# ==================== BOOKING ENDPOINTS ====================

@app.post("/book_travel")
def book_travel(booking: TravelBookingRequest):
    """Create a travel booking"""
    try:
        # Calculate total amount based on service type
        service_type = booking.service_type
        service_details = booking.service_details or "Standard"
        
        if service_type not in SERVICE_PRICES:
            raise ValueError(f"Invalid service type: {service_type}")
        
        if service_details not in SERVICE_PRICES[service_type]:
            service_details = list(SERVICE_PRICES[service_type].keys())[0]
        
        base_price = SERVICE_PRICES[service_type][service_details]
        
        # Calculate duration/nights
        departure = datetime.strptime(booking.departure_date, '%Y-%m-%d')
        if booking.return_date:
            return_date = datetime.strptime(booking.return_date, '%Y-%m-%d')
            duration = (return_date - departure).days
            if duration <= 0:
                raise ValueError("Return date must be after departure date")
        else:
            duration = 1
        
        total_amount = base_price * duration * booking.num_travelers
        
        # Create booking
        booking_data = create_travel_booking(
            customer_email=booking.customer_email,
            service_type=service_type,
            destination=booking.destination,
            departure_date=booking.departure_date,
            return_date=booking.return_date,
            num_travelers=booking.num_travelers,
            service_details=service_details,
            special_requests=booking.special_requests,
            total_amount=total_amount
        )
        
        logger.info(f"📅 Travel booking created for {booking.customer_email}: {service_type} (₹{total_amount})")
        logger.info(f"   📧 Email: {booking.customer_email}")
        logger.info(f"   ✈️ Service: {service_type} - {service_details}")
        logger.info(f"   📅 Dates: {booking.departure_date} to {booking.return_date or 'N/A'}")
        logger.info(f"   👥 Travelers: {booking.num_travelers}")
        logger.info(f"   💵 Total: ₹{total_amount}")
        logger.info(f"   🆔 Booking ID: #{booking_data['booking_id']}")
        
        # Send email notification
        send_booking_confirmation_email(booking.customer_email, booking_data)
        
        return {
            "success": True,
            "booking": booking_data,
            "duration": duration,
            "message": f"Travel booking reserved for {booking.customer_email}! Total: ₹{total_amount}. Payment details to follow.",
            "email_sent": True
        }
        
    except Exception as e:
        logger.error(f"❌ Travel booking error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/flight_classes")
def get_flight_classes():
    """Get available flight class options with pricing"""
    try:
        options = get_flight_class_options()
        return {
            "success": True,
            "flight_classes": options,
            "currency_rate": 83.0,
            "currency_info": "Prices shown in both USD and INR (Indian Rupees)"
        }
    except Exception as e:
        logger.error(f"❌ Error fetching flight classes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/my_bookings/{email}")
def get_my_bookings(email: str):
    """Get all bookings for a customer"""
    try:
        bookings = get_customer_bookings(email)
        return {
            "success": True,
            "bookings": bookings,
            "count": len(bookings)
        }
    except Exception as e:
        logger.error(f"❌ Error fetching bookings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel_booking")
def cancel_booking_endpoint(request: dict):
    """Cancel a booking"""
    try:
        booking_id = request.get('booking_id')
        customer_email = request.get('customer_email')
        
        if not booking_id or not customer_email:
            raise HTTPException(status_code=400, detail="Missing booking_id or customer_email")
        
        result = cancel_booking(booking_id, customer_email)
        
        if result.get('success'):
            logger.info(f"✅ Booking {booking_id} cancelled for {customer_email}")
            return {"success": True, "message": "Booking cancelled successfully"}
        else:
            logger.error(f"❌ Failed to cancel booking {booking_id} for {customer_email}")
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to cancel booking'))
            
    except Exception as e:
        logger.error(f"❌ Cancel booking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel_booking/{booking_id}")
def cancel_booking_endpoint_v2(booking_id: int, customer_email: str):
    """Cancel a booking (alternative endpoint)"""
    try:
        result = cancel_booking(booking_id, customer_email)
        if result['success']:
            logger.info(f"✅ Booking {booking_id} cancelled by {customer_email}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    except Exception as e:
        logger.error(f"❌ Error cancelling booking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reschedule_booking")
def reschedule_booking_endpoint(request: dict):
    """Reschedule a booking"""
    try:
        booking_id = request.get('booking_id')
        customer_email = request.get('customer_email')
        new_departure_date = request.get('new_departure_date')
        new_return_date = request.get('new_return_date')
        
        if not booking_id or not customer_email or not new_departure_date:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        result = reschedule_booking(booking_id, customer_email, new_departure_date, new_return_date)
        
        if result.get('success'):
            logger.info(f"✅ Booking {booking_id} rescheduled for {customer_email}")
            return {"success": True, "message": "Booking rescheduled successfully"}
        else:
            logger.error(f"❌ Failed to reschedule booking {booking_id} for {customer_email}")
            raise HTTPException(status_code=400, detail=result.get('message', 'Failed to reschedule booking'))
            
    except Exception as e:
        logger.error(f"❌ Reschedule booking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reschedule_booking/{booking_id}")
def reschedule_booking_endpoint_v2(booking_id: int, request: dict):
    """Reschedule a booking (alternative endpoint)"""
    try:
        customer_email = request.get('customer_email')
        new_departure_date = request.get('new_departure_date')
        new_return_date = request.get('new_return_date')
        
        if not customer_email:
            raise HTTPException(status_code=400, detail="customer_email is required")
        
        result = reschedule_booking(booking_id, customer_email, new_departure_date, new_return_date)
        if result['success']:
            logger.info(f"✅ Booking {booking_id} rescheduled by {customer_email}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    except Exception as e:
        logger.error(f"❌ Error rescheduling booking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PASSWORD RESET ENDPOINTS ====================

@app.post("/forgot_password")
def forgot_password_endpoint(request: dict):
    """Send password reset email to user"""
    try:
        email = request.get('email')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Check if user exists
        customer = get_or_create_customer(email)
        if not customer:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate reset token (simple implementation - you can make this more secure)
        import secrets
        import time
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token with expiration (you might want to store this in database)
        # For now, we'll just log it and send the email
        logger.info(f"🔐 Password reset requested for: {email}")
        logger.info(f"   Reset token: {reset_token}")
        
        # Send password reset email
        email_sent = send_password_reset_email(email, reset_token)
        
        if email_sent:
            logger.info(f"✅ Password reset email sent to: {email}")
            return {
                "success": True,
                "message": "Password reset email sent successfully",
                "email": email
            }
        else:
            logger.warning(f"⚠️ Password reset email prepared but not sent to: {email}")
            return {
                "success": True,
                "message": "Password reset email prepared (check logs for details)",
                "email": email,
                "note": "Configure SMTP settings to enable email sending",
                "reset_token": reset_token  # Include token for debugging
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Forgot password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/reset_password")
def reset_password_endpoint(request: dict):
    """Reset user password with token"""
    try:
        token = request.get('token')
        email = request.get('email')
        new_password = request.get('new_password')
        
        if not token or not email or not new_password:
            raise HTTPException(status_code=400, detail="Token, email, and new password are required")
        
        # Validate new password
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Check if user exists
        customer = get_or_create_customer(email)
        if not customer:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update password in database
        salt, hashed_password = hash_password(new_password)
        
        # Update customer password in database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE customers 
            SET password_salt = ?, password_hash = ? 
            WHERE email = ?
        """, (salt, hashed_password, email))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Password reset completed for: {email}")
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reset password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== HISTORY ENDPOINTS ====================

@app.get("/chat_history/{email}")
def get_chat_history(email: str):
    """Get chat history for a customer"""
    try:
        conversations = get_conversation_history(email)
        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"❌ Error fetching chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DEBUG ENDPOINTS ====================

@app.get("/debug_user/{email}")
def debug_user_info(email: str):
    """Debug endpoint to check user data in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get customer data
        cursor.execute("""
            SELECT id, email, name, password_salt, password_hash, created_at
            FROM customers WHERE email = ?
        """, (email,))
        
        customer_data = cursor.fetchone()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(customers)")
        schema = cursor.fetchall()
        
        conn.close()
        
        if not customer_data:
            return {"exists": False, "schema": schema}
        
        customer_id, email, name, salt, stored_hash, created_at = customer_data
        return {
            "exists": True,
            "customer_id": customer_id,
            "email": email,
            "name": name,
            "has_salt": bool(salt),
            "has_hash": bool(stored_hash),
            "created_at": created_at,
            "schema": schema
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/test_password")
def test_password_verification(email: str, password: str):
    """Test endpoint to verify password validation is working"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get customer data
        cursor.execute("""
            SELECT id, email, name, password_salt, password_hash, created_at
            FROM customers WHERE email = ?
        """, (email,))
        
        customer_data = cursor.fetchone()
        conn.close()
        
        if not customer_data:
            return {"exists": False, "has_password": False}
        
        customer_id, email, name, salt, stored_hash, created_at = customer_data
        
        if not salt or not stored_hash:
            return {"exists": True, "has_password": False, "message": "User exists but no password set"}
        
        password_correct = verify_password(password, salt, stored_hash)
        return {
            "exists": True, 
            "has_password": True, 
            "password_correct": password_correct,
            "message": "Password correct" if password_correct else "Password incorrect"
        }
        
    except Exception as e:
        return {"error": str(e)}


# ==================== LIVEKIT TOKEN ENDPOINTS ====================
# Unified backend now includes LiveKit token generation (was on port 3000)

class LiveKitTokenRequest(BaseModel):
    roomName: str
    participantName: str
    customerEmail: Optional[EmailStr] = None
    sessionId: Optional[str] = None
    metadata: Optional[Dict] = None


class LiveKitTokenResponse(BaseModel):
    token: str
    url: str
    sessionId: str


class LiveKitTranscriptRequest(BaseModel):
    room_name: str
    speaker: str  # user, assistant, system
    text: str
    session_id: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    language: Optional[str] = "en-US"
    timestamp: Optional[datetime] = None


async def _dispatch_agent_to_room(room_name: str, livekit_url: str, api_key: str, api_secret: str):
    """
    Helper function to dispatch agent to a room
    Uses RoomService to create/update room with agent dispatch
    """
    try:
        import aiohttp
        
        # Create room with agent dispatch using LiveKit HTTP API
        api_url = livekit_url.replace('wss://', 'https://').replace('ws://', 'http://')
        
        # Generate admin token for room operations
        admin_token = AccessToken(api_key, api_secret) \
            .with_grants(VideoGrants(room_create=True, room_admin=True)) \
            .to_jwt()
        
        # Use RoomService CreateRoom API with agent dispatch
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Agent dispatch happens automatically when room is created with participants
        # The agent worker will pick up the room when it detects participants
        
        logger.info(f"✅ Room {room_name} prepared for agent connection")
        logger.info(f"💡 Agent will join when participants connect")
        
    except Exception as e:
        logger.warning(f"⚠️ Room preparation error: {str(e)}")


@app.post("/livekit/get-token", response_model=LiveKitTokenResponse)
async def get_livekit_token(request: LiveKitTokenRequest):
    """
    Generate a LiveKit access token for a participant
    Merged from separate token server (port 3000) into unified backend
    """
    try:
        if not LIVEKIT_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="LiveKit SDK not installed"
            )

        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, api_key, api_secret]):
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured"
            )

        # Generate or reuse a LiveKit session ID
        session_id = request.sessionId or str(uuid.uuid4())

        # Persist mapping for transcripts
        try:
            session_record = record_livekit_session(
                room_name=request.roomName,
                participant_name=request.participantName,
                customer_email=request.customerEmail,
                session_id=session_id,
                metadata=request.metadata
            )
            logger.info(
                "💾 LiveKit session stored: room=%s, session=%s, email=%s",
                session_record.get('room_name', request.roomName),
                session_record.get('session_id'),
                session_record.get('customer_email')
            )
        except Exception as mapping_error:
            logger.warning(f"⚠️ Failed to persist LiveKit session metadata: {mapping_error}")

        # Create token with permissions
        token = AccessToken(api_key, api_secret) \
            .with_identity(request.participantName) \
            .with_name(request.participantName) \
            .with_grants(VideoGrants(
                room_join=True,
                room=request.roomName,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))

        # Generate JWT
        jwt_token = token.to_jwt()

        logger.info(f"✅ LiveKit token generated for {request.participantName} in room {request.roomName}")

        # CRITICAL: Dispatch agent to the room
        # This triggers the agent worker to join and handle voice conversations
        try:
            import aiohttp
            from livekit.api.agent_dispatch_service import AgentDispatchService, CreateAgentDispatchRequest

            dispatch_request = CreateAgentDispatchRequest(
                room=request.roomName,
                agent_name="attar-travel-assistant",
            )

            api_url = livekit_url.replace('wss://', 'https://').replace('ws://', 'http://')

            async with aiohttp.ClientSession() as session:
                dispatch_service = AgentDispatchService(session, api_url, api_key, api_secret)
                dispatch_response = await dispatch_service.create_dispatch(dispatch_request)

            logger.info(f"🤖 Agent dispatched successfully to room {request.roomName}")
            logger.info(f"✅ Dispatch ID: {dispatch_response.id if hasattr(dispatch_response, 'id') else 'N/A'}")

        except Exception as dispatch_error:
            logger.error(f"❌ Agent dispatch failed: {str(dispatch_error)}")
            logger.warning("💡 Make sure agent worker is running: python agent.py dev")

        return LiveKitTokenResponse(
            token=jwt_token,
            url=livekit_url,
            sessionId=session_id
        )

    except Exception as e:
        logger.error(f"❌ Error generating LiveKit token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/livekit/transcript")
async def record_livekit_transcript_endpoint(request: LiveKitTranscriptRequest):
    """Record a transcript message coming from the LiveKit voice agent."""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Transcript text is required")

        session_info = get_livekit_session(request.room_name)
        session_id = request.session_id or (session_info.get('session_id') if session_info else None)
        customer_email = request.customer_email or (session_info.get('customer_email') if session_info else None)

        if not customer_email:
            logger.warning("⚠️ Transcript received without customer email; using guest placeholder")
            customer_email = "guest@livekit.local"

        if not session_id:
            session_id = request.room_name

        language = request.language or "en-US"
        timestamp = request.timestamp or datetime.now()

        logger.info(
            "📝 Transcript captured | room=%s speaker=%s session=%s text=%s",
            request.room_name,
            request.speaker,
            session_id,
            request.text
        )

        save_conversation(
            customer_email,
            session_id,
            request.speaker,
            request.text,
            language,
            timestamp
        )

        update_livekit_session_activity(
            request.room_name,
            customer_email=customer_email,
            last_transcript_at=timestamp
        )

        return {
            "success": True,
            "session_id": session_id,
            "customer_email": customer_email,
            "room_name": request.room_name,
            "speaker": request.speaker,
            "language": language,
            "timestamp": timestamp.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recording LiveKit transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/livekit/transcript/{room_name}")
def get_livekit_transcript_endpoint(room_name: str, limit: int = 200, since_id: Optional[int] = None):
    """Fetch transcript history for a LiveKit room."""
    try:
        transcript_data = get_livekit_transcript(room_name, limit, since_id)
        transcript_data.update({"success": True})
        return transcript_data
    except Exception as e:
        logger.error(f"❌ Error fetching LiveKit transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/livekit/session-info/{room_name}")
def get_livekit_session_info(room_name: str):
    """Return stored metadata for a LiveKit session."""
    try:
        session_info = get_livekit_session(room_name)
        if not session_info:
            raise HTTPException(status_code=404, detail="LiveKit session not found")

        session_info.update({"success": True})
        return session_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving LiveKit session info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/livekit/health")
async def livekit_health_check():
    """LiveKit service health check"""
    return {
        "status": "healthy",
        "livekit_available": LIVEKIT_AVAILABLE,
        "url": os.getenv("LIVEKIT_URL", "not_configured")
    }


@app.get("/livekit", response_class=HTMLResponse)
async def serve_livekit_frontend():
    """
    Serve the LiveKit frontend HTML
    This replaces the separate HTTP server on port 8080
    """
    try:
        livekit_html_path = os.path.join(
            os.path.dirname(__file__), 
            "../livekit_agent/frontend/index.html"
        )
        
        if not os.path.exists(livekit_html_path):
            raise HTTPException(
                status_code=404,
                detail="LiveKit frontend not found"
            )
        
        with open(livekit_html_path, "r") as f:
            html_content = f.read()
        
        # Update the HTML to use the unified backend URL
        html_content = html_content.replace(
            'src="livekit-client.umd.min.js"',
            'src="/livekit/static/livekit-client.umd.min.js"'
        )
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Error serving LiveKit frontend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("✈️  UNIFIED AI TRAVEL AGENT BACKEND")
    print("=" * 60)
    print("🚀 Services:")
    print("   • Azure APIs (Auth, Bookings, Voice)")
    print("   • LiveKit Token Generation")
    print("=" * 60)
    print("📡 Host: 0.0.0.0")
    print("🔌 Port: 8000")
    print("🔊 Azure Voice: Enabled" if LLM_AVAILABLE else "🔊 Azure Voice: Disabled")
    print("🎙️  LiveKit: Enabled" if LIVEKIT_AVAILABLE else "🎙️  LiveKit: Disabled")
    print("=" * 60)
    print("📋 Endpoints:")
    print("   • http://localhost:8000/docs (API documentation)")
    print("   • http://localhost:8000/livekit/get-token (LiveKit tokens)")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


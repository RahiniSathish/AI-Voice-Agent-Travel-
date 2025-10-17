"""
LiveKit Voice Agent with OpenAI Realtime API
Real-time multilingual travel assistant for Saudi Arabia (Attar Travel)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import aiohttp
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import openai

# -----------------------------------------------------
# Load environment variables
# -----------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY in environment variables")

# -----------------------------------------------------
# Logging configuration
# -----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VoiceAssistant")


# =====================================================
# Voice Assistant Class
# =====================================================
class VoiceAssistant:
    """Real-time multilingual voice assistant using OpenAI Realtime API."""

    def __init__(self):
        logger.info("🤖 Voice Assistant initialized with OpenAI Realtime API")
        self.backend_url = self._resolve_backend_url()

    def _resolve_backend_url(self) -> str:
        """Determine backend base URL for storing transcripts."""
        for env_key in ("TRAVEL_BACKEND_URL", "BACKEND_API_URL", "BACKEND_URL"):
            value = os.getenv(env_key)
            if value:
                return value.rstrip('/')
        # Default to local backend
        return "http://localhost:8000"

    async def _fetch_session_info(self, room_name: str) -> Optional[Dict[str, Any]]:
        """Fetch LiveKit session metadata from backend."""
        if not self.backend_url:
            return None

        url = f"{self.backend_url}/livekit/session-info/{room_name}"
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(
                            "📡 Loaded LiveKit session info: room=%s, session=%s, email=%s",
                            room_name,
                            data.get("session_id"),
                            data.get("customer_email")
                        )
                        return data
                    else:
                        logger.warning(
                            "⚠️ Failed to load session info (%s): HTTP %s",
                            room_name,
                            resp.status
                        )
        except Exception as error:
            logger.warning(f"⚠️ Session info request failed for {room_name}: {error}")

        return None

    def _extract_text(self, message: Any) -> Optional[str]:
        """Extract human-readable text from LiveKit/OpenAI message objects."""
        if message is None:
            return None

        if isinstance(message, str):
            return message.strip() or None

        # Some speech events contain a `content` attribute
        content = getattr(message, "content", None)
        if isinstance(content, str):
            content = content.strip()
            if content:
                return content

        # LiveKit RTC speech messages may include alternatives
        alternatives = getattr(message, "alternatives", None)
        if alternatives:
            first = alternatives[0] if isinstance(alternatives, (list, tuple)) and alternatives else None
            if first:
                text_value = getattr(first, "text", None)
                if not text_value and isinstance(first, dict):
                    text_value = first.get("text")
                if text_value:
                    text_value = text_value.strip()
                    if text_value:
                        return text_value

        text_attr = getattr(message, "text", None)
        if isinstance(text_attr, str) and text_attr.strip():
            return text_attr.strip()

        # Fallback for dictionary-like messages
        if isinstance(message, dict):
            for key in ("text", "message", "content"):
                value = message.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        try:
            return str(message).strip()
        except Exception:
            return None

    def _extract_language(self, message: Any) -> Optional[str]:
        """Attempt to detect language metadata from a message."""
        if message is None:
            return None

        for attr in ("language", "language_code", "detected_language"):
            value = getattr(message, attr, None)
            if isinstance(value, str) and value:
                return value

        if isinstance(message, dict):
            for key in ("language", "language_code", "detected_language"):
                value = message.get(key)
                if isinstance(value, str) and value:
                    return value

        return None

    async def _send_transcript(self, *, room_name: str, session_id: Optional[str],
                               customer_email: Optional[str], speaker: str,
                               text: str, language: Optional[str],
                               context: Dict[str, Any]) -> None:
        """Send transcript payload to backend for persistence."""
        if not self.backend_url:
            logger.debug("No backend URL configured; skipping transcript send")
            return

        payload = {
            "room_name": room_name,
            "session_id": session_id,
            "customer_email": customer_email,
            "speaker": speaker,
            "text": text,
            "language": language or "en-US",
            "timestamp": datetime.utcnow().isoformat()
        }

        url = f"{self.backend_url}/livekit/transcript"
        timeout = aiohttp.ClientTimeout(total=5)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status >= 300:
                        error_text = await resp.text()
                        logger.warning(
                            "⚠️ Transcript POST failed (%s): %s",
                            resp.status,
                            error_text
                        )
                    else:
                        data = await resp.json()
                        logger.debug(
                            "💾 Transcript stored: speaker=%s length=%s",
                            speaker,
                            len(text)
                        )
                        if isinstance(data, dict):
                            context["session_id"] = data.get("session_id", context.get("session_id"))
                            context["customer_email"] = data.get("customer_email", context.get("customer_email"))
        except Exception as error:
            logger.warning(f"⚠️ Unable to send transcript to backend: {error}")

    async def entrypoint(self, ctx: JobContext):
        """
        Called when the agent joins a LiveKit room.
        Handles connection, session setup, and AI behavior.
        """
        logger.info(f"🚀 Joining LiveKit room: {ctx.room.name}")

        # Connect to the room
        await ctx.connect()
        logger.info(f"✅ Connected to room: {ctx.room.name}")

        room_name = ctx.room.name
        transcript_context: Dict[str, Any] = {
            "room_name": room_name,
            "session_id": None,
            "customer_email": None,
            "language": "en-US"
        }

        if self.backend_url:
            logger.info(f"📝 Transcript backend: {self.backend_url}")
            session_info = await self._fetch_session_info(room_name)
            if session_info:
                transcript_context["session_id"] = session_info.get("session_id")
                transcript_context["customer_email"] = session_info.get("customer_email")
                if session_info.get("metadata") and isinstance(session_info["metadata"], dict):
                    language_hint = session_info["metadata"].get("language")
                    if language_hint:
                        transcript_context["language"] = language_hint

        # -----------------------------------------------------
        # System Instructions for the Agent
        # -----------------------------------------------------
        instructions = """
You are Alex, a friendly and knowledgeable travel AI assistant powered by Attar Travel expertise.

🌍 You specialize in travel planning for Saudi Arabia.
💬 IMPORTANT: Respond in the SAME language as the user (English, Tamil, Hindi, Telugu, Kannada, or Arabic).
CONVERSATION RULES:
1. Keep responses SHORT (1-2 sentences maximum)
2. Ask ONE question at a time and WAIT for answer
3. Be conversational and friendly like a real human agent
4. DON'T provide long lists or multiple options at once
5. Collect information step-by-step

REQUIRED BOOKING INFORMATION (collect in order):
1. Departure city/airport
2. Arrival city/airport  
3. Travel date
4. Number of passengers
5. Passenger name(s)
6. Contact email
7. Seat preference (window/aisle/no preference)

CONVERSATION FLOW:
Step 1: Ask departure city → WAIT
Step 2: Ask arrival city → WAIT
Step 3: Ask travel date → WAIT
Step 4: Ask number of passengers → WAIT
Step 5: Ask passenger name(s) → WAIT
Step 6: Ask email address → WAIT
Step 7: Ask seat preference → WAIT
Step 8: Confirm all details → WAIT for confirmation
Step 9: Complete booking

Good examples:
✓ "Where are you flying from?"
✓ "And your destination?"
✓ "What date would you like to travel?"
✓ "How many passengers will be traveling?"
✓ "May I have the passenger's full name?"
✓ "What's the best email to send the confirmation to?"
✓ "And a phone number we can reach you at?"
✓ "Window seat, aisle, or no preference?"
✓ "Let me confirm: Flying from New York to London on March 15th for 2 passengers. Is that correct?"

Bad examples:
✗ "I need your departure, arrival, dates, passenger count, names, email, phone, and preferences."
✗ "Here are 5 flight options with different times and prices..."

After collecting all information:
1. Say: "Perfect! Let me process your booking."
2. Provide a COMPLETE booking summary with ALL details:
   - Booking confirmation number (generate a random alphanumeric code like "BK-A1B2C3")
   - Route: [Departure] to [Arrival]
   - Travel date
   - Number of passengers and names
   - Contact information (email and phone)
   - Seat preferences
   - Flight details (you can mention typical airlines and flight times)
3. Thank the passenger and mention confirmation email will be sent

Example summary:
"Your booking is confirmed! Here's your summary:
Booking reference: BK-A1B2C3
Route: New York JFK to London Heathrow
Date: March 15th, 2025
Passengers: 2 - John Smith and Sarah Smith
Contact: john.smith@email.com, phone 555-1234
Seats: Window seats requested
A confirmation email has been sent to your email address. Have a great flight!"

Remember: ONE question at a time, but give a COMPLETE summary at the end.
"""

        # -----------------------------------------------------
        # Initialize the Realtime Model
        # -----------------------------------------------------
        model = openai.realtime.RealtimeModel(
            api_key=OPENAI_API_KEY,
            voice="alloy",       # Options: alloy, shimmer, onyx, nova, fable
            temperature=0.8,
            modalities=["text", "audio"],
        )

        # -----------------------------------------------------
        # Create the AI Agent
        # -----------------------------------------------------
        agent = Agent(
            instructions=instructions,
            llm=model
        )

        # -----------------------------------------------------
        # Create a Live Session (handles user interruptions, speech events, etc.)
        # -----------------------------------------------------
        session = AgentSession(
            allow_interruptions=True,
            min_interruption_duration=0.3,
            min_endpointing_delay=0.4,
            max_endpointing_delay=5.0,
        )

        # -----------------------------------------------------
        # Event Handlers (logging for real-time interaction)
        # -----------------------------------------------------
        def _queue_transcript(speaker: str, raw_message: Any):
            text = self._extract_text(raw_message)
            if not text:
                return

            detected_language = self._extract_language(raw_message)
            if detected_language:
                transcript_context["language"] = detected_language

            asyncio.create_task(
                self._send_transcript(
                    room_name=transcript_context["room_name"],
                    session_id=transcript_context.get("session_id"),
                    customer_email=transcript_context.get("customer_email"),
                    speaker=speaker,
                    text=text,
                    language=transcript_context.get("language"),
                    context=transcript_context
                )
            )

        @session.on("user_speech_started")
        def _on_user_speech_started():
            logger.info("👂 User started speaking...")

        @session.on("user_speech_committed")
        def _on_user_speech_committed(msg):
            text = getattr(msg, 'content', msg)
            logger.info(f"👤 User said: {text}")
            _queue_transcript("user", msg)

        @session.on("agent_speech_started")
        def _on_agent_speech_started():
            logger.info("🗣️ Agent started speaking...")

        @session.on("agent_speech_committed")
        def _on_agent_speech_committed(msg):
            text = getattr(msg, 'content', msg)
            logger.info(f"🤖 Agent said: {text}")
            _queue_transcript("assistant", msg)

        @session.on("agent_speech_interrupted")
        def _on_agent_speech_interrupted():
            logger.info("⚡ User interrupted — AI paused to listen.")

        @session.on("user_state_changed")
        def _on_user_state_changed(state):
            logger.info(f"👥 User state changed: {state}")

        # -----------------------------------------------------
        # Start the assistant session (real-time audio + text streaming)
        # -----------------------------------------------------
        await session.start(agent, room=ctx.room)
        logger.info("🎙️ Voice assistant active — ready for real-time conversation!")

        # Keep the session alive indefinitely
        await asyncio.Event().wait()


# =====================================================
# Job Request Handler
# =====================================================
async def request_handler(job_request: agents.JobRequest):
    """Accepts and handles incoming LiveKit room job requests."""
    logger.info(f"📨 Received job request for room: {job_request.room.name}")
    await job_request.accept()
    logger.info(f"✅ Accepted job request for room: {job_request.room.name}")


# =====================================================
# Entry Point
# =====================================================
if __name__ == "__main__":
    assistant = VoiceAssistant()

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=assistant.entrypoint,
            request_fnc=request_handler,
        )
    )
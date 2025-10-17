"""
Travel AI Agent Alex - Real-Time Continuous Conversation
True voice-to-voice: Start once, then automatic conversation loop
"""

import streamlit as st
import requests
import base64
import tempfile
import os
import json
from datetime import datetime, date, timedelta
import time
import threading
import logging
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import pandas as pd
    import numpy as np
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly not available, using fallback charts")

# Page config
st.set_page_config(
    page_title="Alex - Travel AI Agent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize
BACKEND_URL = "http://localhost:8000"
logger = logging.getLogger(__name__)

# Check for password reset parameters in URL
def check_reset_params():
    """Check if we have password reset parameters in the URL"""
    try:
        # Get query parameters
        query_params = st.query_params
        if 'token' in query_params and 'email' in query_params:
            return query_params['token'], query_params['email']
    except:
        pass
    return None, None

# Handle password reset form
def show_password_reset_form(token, email):
    """Show password reset form"""
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1 style="color: #1e40af; margin-bottom: 10px;">✈️ Attar Travel</h1>
        <h2 style="color: #374151; margin-bottom: 30px;">Reset Your Password</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("password_reset_form"):
        st.markdown(f"**Email:** {email}")
        
        new_password = st.text_input(
            "New Password", 
            type="password",
            placeholder="Enter your new password (min 6 characters)",
            help="Password must be at least 6 characters long"
        )
        
        confirm_password = st.text_input(
            "Confirm New Password", 
            type="password",
            placeholder="Confirm your new password"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            reset_submitted = st.form_submit_button(
                "Reset Password", 
                use_container_width=True,
                type="primary"
            )
        
        if reset_submitted:
            if not new_password or len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
                
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            # Call backend to reset password
            try:
                response = requests.post(
                    f"{BACKEND_URL}/reset_password",
                    json={
                        "token": token,
                        "email": email,
                        "new_password": new_password
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Password reset successfully!")
                    st.info("You can now login with your new password.")
                    
                    # Clear URL parameters and redirect to login
                    st.query_params.clear()
                    st.rerun()
                    
                elif response.status_code == 400:
                    error_data = response.json()
                    st.error(f"❌ {error_data.get('detail', 'Invalid or expired reset token')}")
                else:
                    st.error(f"❌ Reset failed: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    # Back to login button
    if st.button("← Back to Login", use_container_width=True):
        st.query_params.clear()
        st.rerun()

# CSS
st.markdown("""
<style>
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: white;
        display: block !important;
        visibility: visible !important;
        width: 300px !important;
    }
    
    /* Ensure sidebar is always visible */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
    }
    
    .sidebar-content {
        padding: 1rem;
    }
    
    .sidebar-button {
        width: 100%;
        margin-bottom: 0.5rem;
        padding: 0.75rem;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .sidebar-button:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    
    /* Glassmorphism Button Styling - Light Grey Background */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 52px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.6) 100%) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #333333 !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 0 20px !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0px !important;
        visibility: visible !important;
        opacity: 1 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08) !important;
        text-align: center !important;
        position: relative !important;
        overflow: hidden !important;
        min-height: 52px !important;
        max-height: 52px !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Glassmorphism inner highlight effect */
    [data-testid="stSidebar"] .stButton > button::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.6) 50%, transparent 100%) !important;
        z-index: 1 !important;
    }
    
    /* Glassmorphism inner glow */
    [data-testid="stSidebar"] .stButton > button::after {
        content: '' !important;
        position: absolute !important;
        top: 1px !important;
        left: 1px !important;
        right: 1px !important;
        bottom: 1px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%) !important;
        border-radius: 11px !important;
        pointer-events: none !important;
        z-index: 0 !important;
    }
    
    /* Ensure all sidebar buttons are visible and properly spaced */
    [data-testid="stSidebar"] .stButton {
        display: block !important;
        visibility: visible !important;
        margin-bottom: 10px !important;
        width: calc(100% - 20px) !important;
        margin-left: 10px !important;
        margin-right: 10px !important;
    }
    
    /* Glassmorphism hover effect */
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%) !important;
        border-color: rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15), 0 2px 6px rgba(0, 0, 0, 0.1) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
    }
    
    /* Active state */
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.7) 0%, rgba(255, 255, 255, 0.5) 100%) !important;
    }
    
    /* Ensure consistent button height and spacing */
    [data-testid="stSidebar"] .stButton > button:first-child {
        margin-top: 0 !important;
    }
    
    /* Remove any default Streamlit button styling */
    [data-testid="stSidebar"] .stButton > button:focus {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }
    
    /* Ensure proper spacing between buttons */
    [data-testid="stSidebar"] .stButton:not(:last-child) {
        margin-bottom: 10px !important;
    }
    
    /* Ensure consistent button appearance */
    [data-testid="stSidebar"] .stButton > button {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1.2 !important;
        vertical-align: middle !important;
    }
    
    /* Icon styling for glassmorphism effect */
    [data-testid="stSidebar"] .stButton > button {
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stApp {
        background: white;
        background-attachment: fixed;
        min-height: 100vh;
    }
    
    .main-container {
        background: transparent;
        margin: 0;
        padding: 20px;
        border-radius: 0;
        box-shadow: none;
        min-height: auto;
    }
    
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        text-align: center;
    }
    
    .header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        font-weight: bold;
    }
    
    .header p {
        color: white !important;
        margin: 0.5rem 0 0 0;
        text-align: center;
        opacity: 0.9;
        font-size: 1.2rem;
    }
    
    .chat-container {
        background: transparent;
        padding: 1.5rem;
        border-radius: 10px;
        min-height: 400px;
        max-height: 500px;
        overflow-y: auto;
        margin-bottom: 1rem;
    }
    
    .message-emma {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 1rem;
        animation: slideInLeft 0.3s ease-out;
    }
    
    .bubble-emma {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 1px solid #2196f3;
        border-radius: 18px;
        padding: 10px 15px;
        max-width: 85%;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.2);
        position: relative;
        animation: pulse 2s infinite;
    }
    
    .bubble-emma.speaking {
        animation: wave 1.5s infinite;
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
    }
    
    .bubble-emma::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 10px;
        width: 0;
        height: 0;
        border-style: solid;
        border-width: 0 10px 10px 0;
        border-color: transparent #f0f0f5 transparent transparent;
    }
    
    .message-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1rem;
        animation: slideInRight 0.3s ease-out;
    }
    
    .bubble-user {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border: 1px solid #4caf50;
        border-radius: 18px;
        padding: 10px 15px;
        max-width: 85%;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
        position: relative;
    }
    
    .bubble-user.speaking {
        animation: wave 1.5s infinite;
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
    }
    
    .bubble-user::before {
        content: '';
        position: absolute;
        right: -8px;
        top: 10px;
        width: 0;
        height: 0;
        border-style: solid;
        border-width: 10px 0 0 10px;
        border-color: transparent transparent transparent #dcf8c6;
    }
    
    .message-text {
        font-size: 1rem;
        line-height: 1.4;
        color: #000 !important;
        margin: 0;
    }
    
    .message-time {
        font-size: 0.7rem;
        color: #666 !important;
        margin-top: 5px;
        text-align: right;
    }
    
    .sender-name {
        font-weight: bold;
        font-size: 0.9rem;
        margin-bottom: 5px;
        color: #000 !important;
    }
    
    @keyframes slideInLeft {{
        from {{ opacity: 0; transform: translateX(-30px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}

    @keyframes slideInRight {{
        from {{ opacity: 0; transform: translateX(30px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    @keyframes pulse {{
        0% {{
            transform: scale(1);
        }}
        50% {{
            transform: scale(1.02);
        }}
        100% {{
            transform: scale(1);
        }}
    }}

    @keyframes wave {{
        0%, 100% {{
            transform: scale(1) rotate(0deg);
            box-shadow: 0 4px 15px rgba(33, 150, 243, 0.2);
        }}
        25% {{
            transform: scale(1.05) rotate(1deg);
            box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
        }}
        50% {{
            transform: scale(1.08) rotate(0deg);
            box-shadow: 0 8px 25px rgba(33, 150, 243, 0.6);
        }}
        75% {{
            transform: scale(1.05) rotate(-1deg);
            box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
        }}
    }}
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1.2rem;
        font-size: 1.2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    /* Fixed Audio Button */
    .fixed-audio-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        font-size: 2rem;
        cursor: pointer;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .fixed-audio-button:hover {
        transform: scale(1.1);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
    }
    
    .fixed-audio-button.listening {
        animation: pulse 1s infinite;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.4);
    }
    
    .fixed-audio-button.speaking {
        animation: wave 1.5s infinite;
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        box-shadow: 0 10px 30px rgba(78, 205, 196, 0.4);
    }
    
    .stop-button button {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%) !important;
    }
    
    .status-box {
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-size: 0.9rem;
        font-weight: normal;
        margin: 0.5rem 0;
        display: inline-block;
        width: auto;
    }
    
    .listening {
        background: rgba(76, 175, 80, 0.2);
        color: #000 !important;
        border: 1px solid #4CAF50;
    }
    
    .processing {
        background: rgba(255, 152, 0, 0.2);
        color: #000 !important;
        border: 1px solid #FF9800;
    }
    
    .speaking {
        background: rgba(33, 150, 243, 0.2);
        color: #000 !important;
        border: 1px solid #2196F3;
    }
    
    /* Force all text to be black */
    .bubble-emma, .bubble-user, .bubble-emma *, .bubble-user * {
        color: #000 !important;
    }
    
    .bubble-emma p, .bubble-user p, .bubble-emma div, .bubble-user div {
        color: #000 !important;
    }
    
    /* Override any Streamlit default styles */
    .stApp .bubble-emma, .stApp .bubble-user {
        color: #000 !important;
    }
    
    .stApp .bubble-emma *, .stApp .bubble-user * {
        color: #000 !important;
    }
    
    /* Content Cards */
    .content-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    .content-card h3 {
        color: #667eea;
        margin-top: 0;
        font-size: 1.3rem;
    }
    
    .content-card h2 {
        color: #667eea;
        margin: 0;
        font-size: 2rem;
    }
    
    /* Login Screen Styling */
    .login-title {
        color: #000 !important;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .login-info {
        background: #e3f2fd;
        padding: 0.6rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        border-left: 2px solid #2196f3;
        max-width: 320px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .login-info p {
        color: #000 !important;
        margin: 0;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Booking History Styling */
    .booking-title {
        color: #000 !important;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .booking-info {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #ffc107;
    }
    
    .booking-info p {
        color: #000 !important;
        margin: 0;
        font-size: 1rem;
        font-weight: 500;
    }
    
    .booking-suggestion {
        background: #d1ecf1;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #17a2b8;
    }
    
    .booking-suggestion p {
        color: #000 !important;
        margin: 0;
        font-size: 1rem;
        font-weight: 500;
    }
    
    /* Form Labels */
    .stLabel {
        color: #000 !important;
        font-weight: bold;
        font-size: 1.1rem;
    }
    
    /* Login Form Container */
    .login-form-container {
        max-width: 280px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    /* Streamlit Form Elements */
    .login-form-container .stTextInput > div > div > input {
        max-width: 250px !important;
        width: 100% !important;
    }
    
    .login-form-container .stButton > button {
        max-width: 250px !important;
        width: 100% !important;
    }
    
    .login-form-container .stForm {
        max-width: 250px !important;
    }
    
    /* Additional Streamlit overrides */
    .login-form-container .stTextInput {
        max-width: 250px !important;
    }
    
    .login-form-container .stTextInput > div {
        max-width: 250px !important;
    }
    
    .login-form-container .stButton {
        max-width: 250px !important;
    }
    
    .login-form-container .stButton > div {
        max-width: 250px !important;
    }
    
    /* Info and Warning Boxes */
    .stAlert, .stInfo, .stWarning, .stError, .stSuccess {
        color: #000 !important;
    }
    
    .stAlert *, .stInfo *, .stWarning *, .stError *, .stSuccess * {
        color: #000 !important;
    }
    
    /* All Streamlit text elements */
    .stMarkdown, .stText, .stTitle, .stHeader, .stSubheader {
        color: #000 !important;
    }
    
    .stMarkdown *, .stText *, .stTitle *, .stHeader *, .stSubheader * {
        color: #000 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def record_audio(duration=8, sample_rate=16000):
    """Record audio"""
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav
        import numpy as np
        
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='int16',
            blocking=True
        )
        
        # Check if there's actual speech
        audio_level = np.abs(recording).mean()
        if audio_level < 1:  # Very low threshold
            return None
        
        # Save to file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        wav.write(temp_file.name, sample_rate, recording)
        return temp_file.name
    except Exception as e:
        print(f"Recording error: {e}")
        return None

def stop_audio():
    """Stop any playing audio"""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            print("🔇 Audio stopped - pygame mixer stopped")
        else:
            print("🔇 Pygame mixer not initialized")
    except Exception as e:
        print(f"🔇 Error stopping audio: {e}")
        pass

def detect_voice_interruption(duration=0.1, threshold=600):
    """Detect if user starts speaking (voice activity detection)"""
    try:
        import sounddevice as sd
        import numpy as np
        
        # Quick audio sample to check for voice
        recording = sd.rec(
            int(duration * 16000),
            samplerate=16000,
            channels=1,
            dtype='int16',
            blocking=True
        )
        
        # Check audio level
        audio_level = np.abs(recording).mean()
        is_speaking = audio_level > threshold
        if is_speaking:
            print(f"🎤 Voice detected: level={audio_level:.1f}, threshold={threshold}")
        return is_speaking
        
    except Exception as e:
        print(f"⚠️ Voice detection error: {e}")
        return False

def play_audio(audio_bytes, check_interruption=True):
    """Play audio with interruption detection - stops when user starts speaking"""
    try:
        import pygame
        import tempfile
        import os
        import time
        
        # Initialize pygame mixer with better settings for audio quality
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        # Load and play audio
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.set_volume(1.0)  # Set volume to maximum (1.0 = 100%)
        pygame.mixer.music.play()
        
        print(f"🔊 Playing audio... Volume: {pygame.mixer.music.get_volume()}")
        if check_interruption:
            print("   👂 Listening for interruption...")
        
        # Wait for audio to finish, but check for interruptions
        interrupted = False
        check_interval = 0
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Check 10 times per second
            
            # Check for user interruption every 300ms
            if check_interruption:
                check_interval += 1
                if check_interval >= 3:  # Check every ~300ms (3 * 100ms)
                    check_interval = 0
                    if detect_voice_interruption(duration=0.1, threshold=600):
                        print("🛑 USER INTERRUPTION DETECTED - Stopping AI speech")
                        pygame.mixer.music.stop()
                        interrupted = True
                        break
        
        if interrupted:
            print("✅ AI stopped - listening to user")
        else:
            print("✅ Audio playback completed")
        
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass
        
        return not interrupted  # Return False if interrupted
        
    except Exception as e:
        print(f"❌ Audio playback error: {e}")
        import traceback
        traceback.print_exc()
        return False

def transcribe(audio_path):
    """Transcribe audio"""
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': ('audio.wav', f, 'audio/wav')}
            response = requests.post(f"{BACKEND_URL}/transcribe", files=files, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('text', '').strip()
        return None
    except:
        return None

def get_ai_response(text, session_id, customer_email=None):
    """Get AI response and process booking if confirmed"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/voice_chat",
            json={"text": text, "session_id": session_id, "customer_email": customer_email},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get('response', data.get('response_text', ''))
            audio_base64 = data.get('audio_base64')
            
            # Check for booking confirmation in response
            if response_text and "BOOKING_CONFIRMED:" in response_text:
                try:
                    # Extract booking details from response
                    booking_line = [line for line in response_text.split('\n') if 'BOOKING_CONFIRMED:' in line][0]
                    booking_info = booking_line.split('BOOKING_CONFIRMED:')[1].strip()
                    parts = booking_info.split('|')
                    
                    if len(parts) >= 4 and customer_email:
                        service_type = parts[0].strip()
                        destination = parts[1].strip()
                        dates = parts[2].strip()
                        num_travelers = int(parts[3].strip()) if parts[3].strip().isdigit() else 1
                        service_details = parts[4].strip() if len(parts) > 4 else "Standard"
                        
                        # Parse dates
                        if ' to ' in dates:
                            departure_date, return_date = dates.split(' to ')
                        else:
                            departure_date = dates
                            return_date = None
                        
                        # Create booking via API
                        booking_response = requests.post(
                            f"{BACKEND_URL}/book_travel",
                            json={
                                "customer_email": customer_email,
                                "service_type": service_type,
                                "destination": destination,
                                "departure_date": departure_date.strip(),
                                "return_date": return_date.strip() if return_date else None,
                                "num_travelers": num_travelers,
                                "service_details": service_details
                            },
                            timeout=10
                        )
                        
                        if booking_response.status_code == 200:
                            print(f"✅ Booking created successfully via API")
                        
                        # Remove BOOKING_CONFIRMED line from display
                        response_text = '\n'.join([line for line in response_text.split('\n') if 'BOOKING_CONFIRMED:' not in line])
                        
                except Exception as booking_err:
                    print(f"⚠️ Failed to auto-create booking: {booking_err}")
            
            return response_text, audio_base64
        return None, None
    except:
        return None, None

def show_my_bookings():
    """Show customer's bookings (for realtime interface)"""
    st.markdown("""
        <div class="booking-title">
            📋 My Travel Bookings
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Get email from session (should be available since login is required)
    email = st.session_state.get('customer_email')
    if not email:
        st.warning("Please login to view your bookings.")
        return
    
    try:
        response = requests.get(f"{BACKEND_URL}/my_bookings/{email}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get('bookings', [])
            count = data.get('count', 0)
            
            if bookings and len(bookings) > 0:
                st.success(f"Found {len(bookings)} booking(s) for {email}")
                
                for i, booking in enumerate(bookings, 1):
                    # Create a nice box for each booking
                    st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #667eea; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h3 style="color: #667eea; margin-top: 0;">✈️ Booking #{booking['booking_id']}</h3>
                        <p style="margin: 0.5rem 0; font-size: 1.1rem;"><strong>📧 Customer Email:</strong> {email}</p>
                        <p style="margin: 0.5rem 0; font-size: 1.1rem;"><strong>🎯 Service Type:</strong> {booking.get('service_type', 'Travel Service')}</p>
                        <p style="margin: 0.5rem 0;"><strong>🌍 Destination:</strong> {booking.get('destination', 'Saudi Arabia')}</p>
                        <p style="margin: 0.5rem 0;"><strong>📅 Departure Date:</strong> {booking.get('departure_date', booking.get('check_in', 'N/A'))}</p>
                        <p style="margin: 0.5rem 0;"><strong>📅 Return Date:</strong> {booking.get('return_date', booking.get('check_out', 'N/A'))}</p>
                        <p style="margin: 0.5rem 0;"><strong>👥 Number of Travelers:</strong> {booking.get('num_travelers', booking.get('num_guests', 1))}</p>
                        {f'<p style="margin: 0.5rem 0;"><strong>📋 Service Details:</strong> {booking["service_details"]}</p>' if booking.get('service_details') else ''}
                        {f'<p style="margin: 0.5rem 0;"><strong>💬 Special Requests:</strong> {booking["special_requests"]}</p>' if booking.get('special_requests') else ''}
                        <p style="margin: 0.5rem 0; font-size: 1.2rem; color: #667eea;"><strong>💰 Total Amount:</strong> ₹{booking.get('total_amount', 0)}</p>
                        <p style="margin: 0.5rem 0;"><strong>📊 Status:</strong> <span style="color: green; font-weight: bold;">{booking.get('status', 'pending').upper()}</span></p>
                        <p style="font-size: 0.85rem; color: #666; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 0.5rem;">📅 Booked on: {booking.get('created_at', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info(f"💰 Payment details will be provided when you confirm your travel plans")
            else:
                st.markdown("""
                    <div class="booking-info">
                        <p>No travel bookings found for this email address.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                    <div class="booking-suggestion">
                        <p>Talk to Alex and say: 'I want to book a flight to Saudi Arabia' or 'I need accommodation in Riyadh'</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error(f"Failed to load bookings (Status: {response.status_code})")
    except Exception as e:
        st.error(f"Error loading bookings: {e}")

def show_chat_history():
    """Show customer's chat history (for realtime interface)"""
    st.markdown("""
        <div class="booking-title">
            💭 My Chat History
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Get email from session (should be available since login is required)
    email = st.session_state.get('customer_email')
    if not email:
        st.warning("Please login to view your chat history.")
        return
    
    try:
        response = requests.get(f"{BACKEND_URL}/chat_history/{email}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            count = data.get('count', 0)
            
            if conversations and len(conversations) > 0:
                st.success(f"Found {len(conversations)} conversation(s) for {email}")
                
                for i, conversation in enumerate(conversations, 1):
                    # Create a nice box for each conversation
                    st.markdown(f"""
                    <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #4caf50; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <h3 style="color: #4caf50; margin-top: 0;">💬 Conversation #{i}</h3>
                        <p style="margin: 0.5rem 0;"><strong>📅 Date:</strong> {conversation.get('created_at', 'N/A')}</p>
                        <p style="margin: 0.5rem 0;"><strong>💬 User Message:</strong> {conversation.get('user_message', 'N/A')}</p>
                        <p style="margin: 0.5rem 0;"><strong>🤖 Alex Response:</strong> {conversation.get('ai_response', 'N/A')}</p>
                        <p style="font-size: 0.85rem; color: #666; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 0.5rem;">🕒 Duration: {conversation.get('duration', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="booking-info">
                        <p>No chat history found for this email address.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("""
                    <div class="booking-suggestion">
                        <p>Start a conversation with Alex to see your chat history here!</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error(f"Failed to load chat history (Status: {response.status_code})")
    except Exception as e:
        st.error(f"Error loading chat history: {e}")

def check_backend_status():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False

def test_password_validation(email, password):
    """Test password validation for debugging"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/test_password",
            json={"email": email, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {"error": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def login_screen():
    """Customer login screen for realtime interface - Clean minimal design"""
    # Hide sidebar during login
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Main title and subtitle - center-aligned with clean theme
    st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem; max-width: 500px; margin-left: auto; margin-right: auto;">
            <h1 style="color: #1e40af; font-size: 1.8rem; font-weight: bold; margin: 0 0 0.5rem 0; line-height: 1.2;">
                Attar Travel - Saudi Arabia Airlines & Travel Specialist
            </h1>
            <h3 style="color: #374151; font-size: 1.1rem; font-weight: normal; margin: 0;">
                Enter Your Sign in Details →
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Check backend status and show warning
    if not st.session_state.get('backend_status', False):
        st.error("⚠️ Backend server is not running! Please start the backend server first.")
        st.markdown("""
            **To start the backend:**
            1. Open a terminal
            2. Navigate to: `AI Travel Agent/voice/backend/`
            3. Run: `uvicorn travel_main:app --reload`
            
            Or use the provided script: `./start_all.sh`
        """)
        if st.button("🔄 Retry Connection"):
            st.session_state.backend_status = check_backend_status()
            st.session_state.backend_checked = True
            st.rerun()
        return
    
    # Login form with clean background
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        }
        
        .stApp .main .block-container {
            background-color: transparent !important;
            padding: 1rem !important;
            max-width: 100% !important;
        }
        .stForm {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 20px !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2), 0 5px 15px rgba(0, 0, 0, 0.1) !important;
            backdrop-filter: blur(15px) !important;
            -webkit-backdrop-filter: blur(15px) !important;
            max-width: 500px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding: 2.5rem !important;
            animation: formFloat 8s ease-in-out infinite !important;
        }
        
        @keyframes formFloat {
            0%, 100% {
                transform: translateY(0px) scale(1);
            }
            50% {
                transform: translateY(-8px) scale(1.02);
            }
        }
        .stTextInput > div > div > input {
            background-color: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
            font-size: 14px !important;
            color: #333 !important;
            height: 36px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4a90e2 !important;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2) !important;
        }
        
        /* Password field error styling */
        .stTextInput[data-testid="password_input"] > div > div > input {
            transition: all 0.3s ease !important;
        }
        
        .stTextInput[data-testid="password_input"] > div > div > input.error {
            border-color: #ff4444 !important;
            box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.2) !important;
            background-color: #fff5f5 !important;
        }
        .stTextInput label {
            color: #333 !important;
            font-weight: 500 !important;
            font-size: 14px !important;
        }
        .stButton > button {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            width: 100% !important;
            height: 48px !important;
            box-shadow: 0 4px 15px rgba(30, 64, 175, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(30, 64, 175, 0.4) !important;
        }
        
        /* Button layout styling for login form */
        .stForm .stButton {
            margin-bottom: 0.5rem !important;
        }
        
        /* Make all buttons in login form the same size */
        .stForm .stButton > button {
            height: 48px !important;
            font-size: 14px !important;
            padding: 12px 24px !important;
            margin: 0 !important;
        }
        
        /* Ensure both buttons are equal width */
        .stForm .stButton {
            width: 100% !important;
        }
        
        /* Button focus and active states */
        .stButton > button:focus {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.3) !important;
        }
        
        .stButton > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 10px rgba(30, 64, 175, 0.3) !important;
        }
        
        /* Style the forgot password button to look like a text link */
        .stButton[data-testid="forgot_password_text_link"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        
        .stButton[data-testid="forgot_password_text_link"] > button {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            color: #1e40af !important;
            text-decoration: underline !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 8px 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            text-align: center !important;
            width: auto !important;
            height: auto !important;
            min-height: auto !important;
            border-radius: 0 !important;
            outline: none !important;
        }
        
        .stButton[data-testid="forgot_password_text_link"] > button:hover {
            background: transparent !important;
            background-color: transparent !important;
            color: #1d4ed8 !important;
            text-decoration: none !important;
            transform: none !important;
            box-shadow: none !important;
            border: none !important;
        }
        
        .stButton[data-testid="forgot_password_text_link"] > button:focus {
            background: transparent !important;
            background-color: transparent !important;
            color: #1d4ed8 !important;
            text-decoration: none !important;
            box-shadow: none !important;
            border: none !important;
            outline: none !important;
        }
        
        .stButton[data-testid="forgot_password_text_link"] > button:active {
            background: transparent !important;
            background-color: transparent !important;
            color: #1d4ed8 !important;
            text-decoration: none !important;
            transform: none !important;
            box-shadow: none !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize action state
    if 'auth_action' not in st.session_state:
        st.session_state.auth_action = None
    
    # Help text will be moved to bottom after buttons
    
    # Form layout with compact columns for labels and inputs
    with st.form("login_form"):
        # Email field
        email_col1, email_col2 = st.columns([1, 2])
        with email_col1:
            st.markdown('<div style="display: flex; align-items: center; height: 36px; color: #333; font-weight: 500; font-size: 14px;">Email</div>', unsafe_allow_html=True)
        with email_col2:
            email = st.text_input("Email", placeholder="your.email@example.com", label_visibility="collapsed", key="email_input")
        
        # Password field
        pwd_col1, pwd_col2 = st.columns([1, 2])
        with pwd_col1:
            st.markdown('<div style="display: flex; align-items: center; height: 36px; color: #333; font-weight: 500; font-size: 14px;">Password</div>', unsafe_allow_html=True)
        with pwd_col2:
            password = st.text_input("Password", placeholder="Password", type="password", label_visibility="collapsed", key="password_input")
            
            # Clear password error flag when user starts typing
            if password and st.session_state.get('password_error', False):
                st.session_state.password_error = False
        
        # Name field
        name_col1, name_col2 = st.columns([1, 2])
        with name_col1:
            st.markdown('<div style="display: flex; align-items: center; height: 36px; color: #333; font-weight: 500; font-size: 14px;">Full Name <span style="color: #999; font-size: 0.85em;">(New users)</span></div>', unsafe_allow_html=True)
        with name_col2:
            name = st.text_input("Name", placeholder="Full Name (New users only)", label_visibility="collapsed", key="name_input")
        
        # Add some spacing before buttons
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Two separate buttons - Sign In and Login
        button_col1, gap, button_col2 = st.columns([1, 0.1, 1])
        
        with button_col1:
            signin_button = st.form_submit_button("Sign In (New User)", use_container_width=True)
        
        with button_col2:
            login_button = st.form_submit_button("Login", use_container_width=True)
        
        # Form submitted - process login/registration
        
        if signin_button or login_button:
            # Determine action
            is_signin = signin_button
            
            # Validation
            if not email:
                st.error("❌ Please enter your email address")
                logger.warning("Authentication attempt with empty email")
                return
            
            if not password:
                st.error("❌ **Password Required**")
                st.warning("🔒 Please enter your password.")
                logger.warning(f"Authentication attempt without password for: {email}")
                return
            
            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                st.error("❌ Please enter a valid email address")
                logger.warning(f"Invalid email format: {email}")
                return
            
            # Password validation for Sign In (Registration)
            if is_signin:
                # Check password requirements: at least 6 characters, special characters, numbers
                has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
                has_number = bool(re.search(r'\d', password))
                has_min_length = len(password) >= 6
                
                if not has_min_length or not has_special or not has_number:
                    st.warning("⚠️ **Password Requirements Not Met**")
                    st.markdown("""
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                        <p style="margin: 0 0 0.5rem 0; color: #856404;"><strong>Password must contain:</strong></p>
                        <ul style="margin: 0; color: #856404;">
                            <li>✓ At least 6 characters</li>
                            <li>✓ At least one number (0-9)</li>
                            <li>✓ At least one special character (!@#$%^&*)</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    logger.warning(f"Sign In attempt with weak password for: {email}")
                    return
                
                if not name:
                    st.error("❌ Please enter your full name to register")
                    logger.warning(f"Sign In attempt without name for: {email}")
                    return
            
            # For login, just check minimum password length
            if not is_signin and len(password) < 3:
                st.error("❌ **Password Too Short**")
                st.warning("🔒 Password must be at least 3 characters long.")
                logger.warning(f"Login attempt with very short password for: {email}")
                return
            
            try:
                # Check if user exists first
                check_response = requests.get(f"{BACKEND_URL}/check_customer/{email}", timeout=10)
                user_exists = check_response.status_code == 200 and check_response.json().get('exists', False)
                
                if is_signin:
                    # SIGN IN (REGISTRATION) MODE
                    if user_exists:
                        st.error("❌ This email is already registered. Please use Login button instead.")
                        logger.warning(f"Sign In attempt with existing email: {email}")
                        return
                    
                    # Register new user
                    with st.spinner("Creating your account..."):
                        response = requests.post(
                            f"{BACKEND_URL}/register",
                            json={"email": email, "password": password, "full_name": name},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.customer_email = email
                            st.session_state.customer_name = name
                            st.session_state.customer_data = data.get('customer', {})
                            st.session_state.logged_in = True
                            
                            # Show toast message for successful registration
                            st.toast("✅ Successfully registered!")
                            st.success(f"✅ Successfully registered! Welcome {name}!")
                            
                            logger.info(f"✅ New user registered: {email} - {name}")
                            print(f"✅ INFO: New user registered: {email} - {name}")
                            time.sleep(1)  # Brief pause to show the toast
                            st.rerun()
                        else:
                            error_msg = response.json().get('detail', 'Registration failed. Please try again.')
                            st.error(f"❌ Registration failed: {error_msg}")
                            logger.error(f"Registration failed for {email}: {error_msg}")
                else:
                    # LOGIN MODE
                    if not user_exists:
                        st.error("❌ This email is not registered. Please sign in first.")
                        logger.warning(f"Login attempt with unregistered email: {email}")
                        print(f"⚠️ WARNING: Login attempt with unregistered email: {email}")
                        st.info("💡 Click 'Sign In (New User)' button to create an account")
                        return
                    
                    # Login existing user
                    with st.spinner("Logging in..."):
                        print(f"🔐 Attempting login for: {email}")
                        print(f"🔐 Password length: {len(password)} characters")
                        response = requests.post(
                            f"{BACKEND_URL}/login",
                            json={"email": email, "password": password, "name": name or email.split('@')[0]},
                            timeout=10
                        )
                        print(f"🔐 Login response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            data = response.json()
                            customer_data = data.get('customer', {})
                            st.session_state.customer_email = email
                            st.session_state.customer_name = customer_data.get('name', email.split('@')[0])
                            st.session_state.customer_data = customer_data
                            st.session_state.logged_in = True
                            st.success(f"✅ Welcome back {st.session_state.customer_name}!")
                            logger.info(f"✅ User logged in: {email}")
                            print(f"✅ INFO: User logged in: {email}")
                            st.rerun()
                        elif response.status_code == 401:
                            # Unauthorized - wrong password or no password set
                            error_detail = response.json().get('detail', 'Invalid password')
                            st.session_state.password_error = True  # Set error flag
                            
                            if "Password not set" in error_detail:
                                st.error("❌ **Login Failed: Password Not Set**")
                                st.warning("🔒 This account was created before password security was implemented.")
                                st.info("💡 **Solution:** Please use 'Sign In (New User)' button with a new password to secure your account.")
                            else:
                                st.error("❌ **Login Failed: Incorrect Password**")
                                st.warning("🔒 The password you entered is incorrect. Please check your password and try again.")
                                st.info("💡 **Tips:**\n- Make sure Caps Lock is not enabled\n- Check for any typing errors\n- If you forgot your password, you may need to sign in again with 'Sign In (New User)' button")
                            
                            # Show a retry suggestion
                            st.markdown("""
                            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                                <p style="margin: 0; color: #856404;"><strong>🔄 Try Again:</strong></p>
                                <ul style="margin: 0.5rem 0 0 0; color: #856404;">
                                    <li>Double-check your password</li>
                                    <li>Ensure Caps Lock is off</li>
                                    <li>Try typing your password slowly</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            logger.warning(f"Login failed for {email}: Wrong password entered")
                            print(f"⚠️ WARNING: Login failed for {email}: Wrong password entered")
                        elif response.status_code == 404:
                            # User not found
                            st.error("❌ User not found. Please sign in first.")
                            st.info("💡 Click 'Sign In (New User)' button to create an account")
                            logger.warning(f"Login attempt for non-existent user: {email}")
                            print(f"⚠️ WARNING: Login attempt for non-existent user: {email}")
                        else:
                            error_msg = response.json().get('detail', 'Login failed. Please try again.')
                            st.error(f"❌ Login failed: {error_msg}")
                            logger.error(f"Login failed for {email}: {error_msg}")
                            print(f"❌ ERROR: Login failed for {email}: {error_msg}")
                        
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to server. The backend is not running.")
                st.markdown("Please run: `python3 start_backend.py` from the backend directory")
                st.session_state.backend_status = False
                logger.error("Backend connection error")
                print("❌ ERROR: Backend connection error")
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out. Please try again.")
                logger.error("Login request timeout")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Login/Registration error: {str(e)}")
                print(f"❌ ERROR: Login/Registration error: {str(e)}")
    
    # Forgot Password - Centered below the login form
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Forgot Password?", key="forgot_password_text_link", help="Click to reset password"):
            st.session_state.show_forgot_password = True
            st.rerun()
    
    st.markdown("""
    </div>
    """, unsafe_allow_html=True)
    
    # Forgot Password Section - Only show when button is clicked
    if st.session_state.get('show_forgot_password', False):
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; margin: 1rem 0;">
            <h4 style="color: #1e40af; margin: 0;">🔐 Forgot Your Password?</h4>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("forgot_password_form"):
            forgot_email = st.text_input("Email Address", placeholder="Enter your registered email", key="forgot_email_input")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                forgot_submit = st.form_submit_button("Send Reset Link", use_container_width=True)
            with col3:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_forgot_password = False
                    st.rerun()
        
        if forgot_submit:
            if not forgot_email:
                st.error("❌ Please enter your email address")
            else:
                # Validate email format
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, forgot_email):
                    st.error("❌ Please enter a valid email address")
                else:
                    try:
                        # Check if user exists
                        check_response = requests.get(f"{BACKEND_URL}/check_customer/{forgot_email}", timeout=10)
                        user_exists = check_response.status_code == 200 and check_response.json().get('exists', False)
                        
                        if user_exists:
                            # Send password reset email
                            try:
                                reset_response = requests.post(
                                    f"{BACKEND_URL}/forgot_password",
                                    json={"email": forgot_email},
                                    timeout=10
                                )
                                
                                if reset_response.status_code == 200:
                                    response_data = reset_response.json()
                                    if response_data.get('note'):
                                        # SMTP not configured - show helpful message
                                        st.warning("⚠️ Password reset email prepared but not sent")
                                        st.info("📧 **Email system is ready but needs configuration.**")
                                        st.markdown("""
                                        **To enable email sending:**
                                        1. Create a `.env` file in the backend directory
                                        2. Add your email SMTP settings:
                                           ```
                                           SMTP_SERVER=smtp.gmail.com
                                           SMTP_PORT=587
                                           SMTP_USERNAME=your-email@gmail.com
                                           SMTP_PASSWORD=your-app-password
                                           SMTP_FROM_EMAIL=your-email@gmail.com
                                           ```
                                        3. Restart the backend server
                                        
                                        **Check the EMAIL_SETUP_INSTRUCTIONS.md file for detailed setup guide.**
                                        """)
                                        
                                        # Show the reset token for testing
                                        if 'reset_token' in response_data:
                                            st.code(f"Reset Token: {response_data['reset_token']}")
                                        
                                        logger.info(f"✅ Password reset email prepared for: {forgot_email}")
                                    else:
                                        # Email was actually sent
                                        st.success("✅ Password reset link sent to your email!")
                                        st.info("📧 Please check your email and follow the instructions to reset your password.")
                                        logger.info(f"✅ Password reset email sent to: {forgot_email}")
                                    
                                    # Hide the forgot password section after submission
                                    st.session_state.show_forgot_password = False
                                    st.rerun()
                                else:
                                    # Handle different error status codes
                                    try:
                                        error_data = reset_response.json()
                                        error_msg = error_data.get('detail', 'Unknown error')
                                        st.error(f"❌ {error_msg}")
                                    except:
                                        st.error(f"❌ Failed to send reset email. Server returned status {reset_response.status_code}")
                                    logger.error(f"Failed to send password reset email to: {forgot_email}, Status: {reset_response.status_code}")
                                    
                            except requests.exceptions.RequestException as req_err:
                                st.error("❌ Cannot connect to server. Please try again later.")
                                logger.error(f"Request error during password reset: {req_err}")
                            except Exception as reset_err:
                                st.error(f"❌ Error: {str(reset_err)}")
                                logger.error(f"Password reset error: {reset_err}")
                        else:
                            st.error("❌ This email is not registered with us.")
                            st.info("💡 Please check your email address or sign up for a new account.")
                            logger.warning(f"Password reset attempt for unregistered email: {forgot_email}")
                            
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to server. Please try again later.")
                        logger.error("Backend connection error during password reset")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        logger.error(f"Password reset error: {str(e)}")
    
    # Instructions at the bottom - left aligned
    st.markdown("""
    <div style="text-align: left; margin-top: 1rem; padding-top: 0.5rem; border-top: 1px solid #eee; max-width: 500px; margin-left: auto; margin-right: auto;">
        <p style="color: #333; font-size: 13px; margin: 0 0 0.3rem 0; line-height: 1.3;"><strong>Instructions:</strong></p>
        <ul style="color: #666; font-size: 12px; margin: 0; line-height: 1.3; padding-left: 1rem;">
            <li><strong>New User:</strong> All fields required (Email, Password, Full Name)</li>
            <li><strong>Existing User:</strong> Email & Password (Full Name optional)</li>
            <li><strong>Password:</strong> 6+ chars, numbers & special chars</li>
        </ul>
        <p style="color: #666; font-size: 12px; margin: 0.5rem 0 0 0;">Need help? Contact support</p>
    </div>
    """, unsafe_allow_html=True)

def sidebar_navigation():
    """Create beautiful sidebar navigation with styled buttons"""
    with st.sidebar:
        # Header
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="color: #333333; margin: 0; font-size: 1.5rem;">🏢 Attar Travel</h2>
                <p style="color: #666666; margin: 0.5rem 0 0 0; font-size: 0.9rem;">Saudi Arabia Travel Specialist</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Clean button section without navigation header
        
        # Dashboard Button (first)
        if st.button("Dashboard", key="sidebar_dashboard", use_container_width=True):
            # Stop any ongoing AI voice conversation and audio playback
            print("🛑 Dashboard button clicked - stopping audio and conversation")
            stop_audio()
            st.session_state.conversation_running = False
            st.session_state.current_view = 'dashboard'
            st.session_state.show_bookings = False
            st.session_state.show_chat_history = False
            st.rerun()
        
        # Chat/Conversation Button (removed)
        if False and st.button("Chat", key="sidebar_chat", use_container_width=True):
            # Return to conversation view and load chat history from database
            print("💬 Chat button clicked - stopping audio and loading conversation history")
            
            # Stop any ongoing AI voice conversation and audio playback
            stop_audio()
            st.session_state.conversation_running = False
            
            # Load chat history from backend
            email = st.session_state.get('customer_email')
            if email:
                try:
                    response = requests.get(f"{BACKEND_URL}/chat_history/{email}", timeout=10)
                    print(f"📡 Backend response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        conversations = data.get('conversations', [])
                        print(f"📊 Found {len(conversations)} conversations in database")
                        
                        # Clear and reload chat history
                        st.session_state.chat_history = []
                        
                        if conversations and len(conversations) > 0:
                            for idx, conv in enumerate(conversations):
                                print(f"  📝 Loading conversation {idx + 1}: {conv.get('user_message', '')[:50]}...")
                                
                                # Extract timestamp
                                created_at = conv.get('created_at', '')
                                time_str = ''
                                if created_at:
                                    try:
                                        # Handle different timestamp formats
                                        if ' ' in created_at:
                                            time_str = created_at.split(' ')[1][:5]  # Extract HH:MM
                                        else:
                                            time_str = created_at[:5]
                                    except:
                                        time_str = created_at[:16] if len(created_at) >= 16 else created_at
                                
                                # Add user message
                                user_msg = conv.get('user_message', '')
                                if user_msg:
                                    st.session_state.chat_history.append({
                                        'role': 'User',
                                        'text': user_msg,
                                        'time': time_str
                                    })
                                
                                # Add AI response
                                ai_msg = conv.get('ai_response', '')
                                if ai_msg:
                                    st.session_state.chat_history.append({
                                        'role': 'Alex',
                                        'text': ai_msg,
                                        'time': time_str
                                    })
                            
                            print(f"✅ Successfully loaded {len(st.session_state.chat_history)} messages into chat")
                        else:
                            print("⚠️ No conversations found in database")
                    else:
                        print(f"❌ Failed to fetch chat history: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error loading chat history: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️ No email found in session state")
            
            st.session_state.current_view = 'conversation'
            st.session_state.show_bookings = False
            st.session_state.show_chat_history = False
            st.rerun()
        
        # My Bookings Button (fourth)
        if st.button("My Bookings", key="sidebar_bookings", use_container_width=True):
            try:
                # Stop any ongoing AI voice conversation and audio playback
                print("🛑 My Bookings button clicked - stopping audio and conversation")
                stop_audio()
                st.session_state.conversation_running = False
                st.session_state.show_bookings = not st.session_state.get('show_bookings', False)
                st.session_state.current_view = 'conversation'
                st.session_state.show_chat_history = False
                st.rerun()
            except Exception as e:
                st.error(f"Error with My Bookings button: {e}")
        
        # Chat History Button (fifth)
        if st.button("Chat History", key="sidebar_chat_history", use_container_width=True):
            try:
                # Stop any ongoing AI voice conversation and audio playback
                print("🛑 Chat History button clicked - stopping audio and conversation")
                stop_audio()
                st.session_state.conversation_running = False
                st.session_state.show_chat_history = not st.session_state.get('show_chat_history', False)
                st.session_state.current_view = 'conversation'
                st.session_state.show_bookings = False
                st.rerun()
            except Exception as e:
                st.error(f"Error with Chat History button: {e}")
        
        # Logout Button (sixth)
        if st.button("Logout", key="sidebar_logout", use_container_width=True):
            # Stop any ongoing AI voice conversation and audio playback
            print("🛑 Logout button clicked - stopping audio and conversation")
            stop_audio()
            st.session_state.conversation_running = False
            for key in list(st.session_state.keys()):
                if key not in ['session_id']:
                    del st.session_state[key]
            st.rerun()
        
        # Separator
        st.markdown("---")
        
        # User Info
        customer_name = st.session_state.get('customer_name', 'Guest')
        customer_email = st.session_state.get('customer_email', 'No email')
        st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.6); border-radius: 8px; color: #333333;">
                <p style="color: #333333; margin: 0 0 0.3rem 0; font-size: 0.9rem; font-weight: bold;">Logged in as:</p>
                <p style="color: #333333; margin: 0; font-size: 0.9rem;">{customer_name}</p>
                <p style="color: #666666; margin: 0; font-size: 0.8rem;">{customer_email}</p>
            </div>
        """, unsafe_allow_html=True)

def get_dashboard_stats(email):
    """Get dashboard statistics"""
    stats = {
        'total_bookings': 0,
        'cancelled_bookings': 0,
        'total_spent': 0,
        'upcoming_trips': 0
    }
    
    try:
        # Get bookings
        response = requests.get(f"{BACKEND_URL}/my_bookings/{email}", timeout=10)
        if response.status_code == 200:
            bookings = response.json().get('bookings', [])
            # Only count active bookings (exclude cancelled)
            active_bookings = [b for b in bookings if b.get('status', '').lower() != 'cancelled']
            cancelled_bookings = [b for b in bookings if b.get('status', '').lower() == 'cancelled']
            
            stats['total_bookings'] = len(active_bookings)
            stats['cancelled_bookings'] = len(cancelled_bookings)
            stats['total_spent'] = sum(booking.get('total_amount', 0) for booking in active_bookings)
            # Count upcoming trips (status = confirmed or pending)
            stats['upcoming_trips'] = sum(1 for b in active_bookings if b.get('status', '').lower() in ['confirmed', 'pending'])
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
    
    return stats

def get_booking_analytics(email):
    """Get detailed booking analytics for charts and insights"""
    analytics = {
        'status_distribution': {},
        'monthly_spending': [],
        'top_destinations': [],
        'recent_bookings': []
    }
    
    try:
        response = requests.get(f"{BACKEND_URL}/my_bookings/{email}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get('bookings', [])
            
            if bookings:
                # Status distribution
                status_counts = {}
                monthly_totals = {}
                destination_counts = {}
                
                for booking in bookings:
                    # Count statuses
                    status = booking.get('status', 'pending')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Monthly spending
                    try:
                        booking_date = datetime.strptime(booking.get('created_at', ''), '%Y-%m-%d %H:%M:%S.%f')
                        month_key = booking_date.strftime('%b %Y')
                        amount = float(booking.get('total_amount', 0))
                        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + amount
                    except:
                        pass
                    
                    # Destination counts
                    destination = booking.get('destination', 'Unknown')
                    destination_counts[destination] = destination_counts.get(destination, 0) + 1
                    
                    # Recent bookings (last 3)
                    if len(analytics['recent_bookings']) < 3:
                        analytics['recent_bookings'].append({
                            'service_type': booking.get('service_type', 'Travel Service'),
                            'destination': destination,
                            'departure_date': booking.get('departure_date', 'N/A'),
                            'status': status,
                            'amount': booking.get('total_amount', 0)
                        })
                
                analytics['status_distribution'] = status_counts
                
                # Convert monthly totals to list format
                for month, amount in monthly_totals.items():
                    analytics['monthly_spending'].append({'month': month, 'amount': amount})
                
                # Convert destination counts to list format
                for dest, count in destination_counts.items():
                    analytics['top_destinations'].append({'destination': dest, 'count': count})
                
                # Sort by count
                analytics['top_destinations'].sort(key=lambda x: x['count'], reverse=True)
                analytics['monthly_spending'].sort(key=lambda x: x['month'])
    
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
    
    return analytics


def show_voice_chat_interface():
    """Show LiveKit Voice Chat Interface - Real-time voice conversations"""
    import streamlit.components.v1 as components
    
    # Get customer info
    customer_name = st.session_state.get('customer_name', 'Guest')
    customer_email = st.session_state.get('customer_email', 'guest@example.com')
    
    # Generate unique room name and participant name
    import uuid
    room_name = f"attar-travel-{uuid.uuid4().hex[:8]}"
    participant_name = customer_name.replace(' ', '_')
    
    # Voice Chat Header
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; 
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);">
            <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: 600; text-align: center;">
                 Attar Travel AI Agent
            </h1>
            <p style="color: rgba(255,255,255,0.95); margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1rem;">
                Talk to our AI Travel Consultant about Saudi Arabia
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    with st.expander("📖 How to use Voice Chat", expanded=True):
        st.markdown("""
        **Voice Chat is powered by LiveKit & OpenAI Realtime API**
        
        1. Click **"Connect & Start Talking"** button below
        2. Allow microphone access when prompted by your browser
        3. Start speaking naturally - the AI will respond in real-time
        4. The AI can be interrupted at any time - just start speaking!
        5. Ask about destinations, packages, bookings, or travel tips
        
        **Tips for best experience:**
        - Use a headset or earphones to avoid echo
        - Speak clearly and naturally
        - The AI understands multiple languages
        - You can interrupt the AI at any time
        """)
    
    # LiveKit Voice Interface (HTML/JavaScript)
    livekit_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Chat</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }}
        .voice-container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .status {{
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .status.disconnected {{ background: #f3f4f6; color: #6b7280; }}
        .status.connecting {{ background: #fef3c7; color: #92400e; }}
        .status.connected {{ background: #d1fae5; color: #065f46; }}
        .status.active {{ background: #dbeafe; color: #1e40af; }}
            
        .controls {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin: 2rem 0;
            align-items: center;
        }}
        button {{
            padding: 0.8rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            max-width: 200px;
            width: 100%;
        }}
        .connect-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .connect-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }}
        .disconnect-btn {{
            background: #ef4444;
            color: white;
            display: none;
        }}
        .disconnect-btn:hover {{
            background: #dc2626;
        }}
        .transcript-container {{
            margin-top: 1.5rem;
            background: #ffffff;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(15, 23, 42, 0.08);
        }}
        .transcript-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }}
        .transcript-header h3 {{
            margin: 0;
            font-size: 1.1rem;
            color: #1e293b;
        }}
        .transcript-status {{
            font-size: 0.8rem;
            color: #475569;
        }}
        .transcript-content {{
            max-height: 250px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        .transcript-item {{
            background: #f8fafc;
            border-radius: 10px;
            padding: 0.75rem;
            border-left: 4px solid #6366f1;
            box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.1);
        }}
        .transcript-item.user {{
            border-left-color: #0ea5e9;
        }}
        .transcript-item.agent {{
            border-left-color: #8b5cf6;
        }}
        .transcript-item.system {{
            border-left-color: #f59e0b;
        }}
        .transcript-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #475569;
            margin-bottom: 0.25rem;
        }}
        .transcript-message {{
            font-size: 0.95rem;
            color: #1e293b;
            line-height: 1.4;
        }}
        .transcript-time {{
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 0.35rem;
        }}
            .info {{
                background: #f0f9ff;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border-left: 4px solid #3b82f6;
            }}
            .info-label {{
                font-weight: 600;
                color: #1e40af;
                margin-bottom: 0.3rem;
            }}
            .visualizer {{
                width: 100%;
                height: 100px;
                background: #f9fafb;
                border-radius: 8px;
                margin: 1rem 0;
                display: none;
                align-items: center;
                justify-content: center;
            }}
            .visualizer.visible {{
                display: flex;
            }}
            .wave {{
                width: 4px;
                height: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0 3px;
                border-radius: 2px;
                animation: wave 1.5s ease-in-out infinite;
            }}
            .wave:nth-child(2) {{ animation-delay: 0.1s; }}
            .wave:nth-child(3) {{ animation-delay: 0.2s; }}
            .wave:nth-child(4) {{ animation-delay: 0.3s; }}
            .wave:nth-child(5) {{ animation-delay: 0.4s; }}
            @keyframes wave {{
                0%, 100% {{ height: 20px; }}
                50% {{ height: 60px; }}
            }}
        </style>
    </head>
    <body>
        <div class="voice-container">
            <div id="status" class="status disconnected">● Not Connected</div>
            
            <div id="visualizer" class="visualizer">
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
            </div>
            
            <div class="controls">
                <button id="connectBtn" class="connect-btn" onclick="connect()">
                    Speak
                </button>
                <button id="disconnectBtn" class="disconnect-btn" onclick="disconnect()">
                    End call
                </button>
            </div>

            <div class="transcript-container" id="transcriptContainer">
                <div class="transcript-header">
                    <h3>Conversation Transcript</h3>
                    <span id="transcriptStatus" class="transcript-status">Waiting to start...</span>
                </div>
                <div id="transcriptContent" class="transcript-content"></div>
            </div>
        </div>

        <script>
            // Try multiple possible global variable names
            window.LiveKitGlobalCheck = function() {{
                console.log("[DEBUG] Checking possible LiveKit global variables...");
                console.log("window.LiveKit:", typeof window.LiveKit);
                console.log("window.LivekitClient:", typeof window.LivekitClient);
                console.log("window.livekit:", typeof window.livekit);

                // Try to find the correct global variable
                if (typeof window.LiveKit !== 'undefined') {{
                    window.LiveKitGlobal = window.LiveKit;
                    console.log("[SUCCESS] Found LiveKit as window.LiveKit");
                }} else if (typeof window.LivekitClient !== "undefined") {{
                    window.LiveKitGlobal = window.LivekitClient;
                    console.log("[SUCCESS] Found LiveKit as window.LivekitClient");
                }} else if (typeof window.livekit !== "undefined") {{
                    window.LiveKitGlobal = window.livekit;
                    console.log("[SUCCESS] Found LiveKit as window.livekit");
                }} else {{
                    console.log("[ERROR] No LiveKit global variable found");
                }}
            }};

            // Load script and check after loading
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/livekit-client@2.0.0/dist/livekit-client.umd.min.js?v=2.0.0';
            script.onload = function() {{
                console.log("[SUCCESS] LiveKit SDK script loaded");
                setTimeout(window.LiveKitGlobalCheck, 100);
            }};
            script.onerror = function() {{
                console.error("[ERROR] Failed to load LiveKit SDK script");
            }};
            document.head.appendChild(script);
        </script>
        <script>
            let room;
            let isConnected = false;
            const roomName = '{room_name}';
            const participantName = '{participant_name}';
            const backendUrl = {backend_url_json};
            const customerEmail = {customer_email_json};
            let currentSessionId = null;
            let transcriptInterval = null;
            let lastTranscriptId = null;
            const renderedTranscriptIds = new Set();

            // Check if LiveKit SDK is loaded
            function checkLiveKitLoaded() {{
                console.log("[DEBUG] Checking LiveKit SDK...");
                console.log("window.LiveKitGlobal type:", typeof window.LiveKitGlobal);
                console.log("window.LiveKitGlobal.Room type:", typeof window.LiveKitGlobal?.Room);

                if (typeof window.LiveKitGlobal !== "undefined" && window.LiveKitGlobal.Room) {{
                    console.log("[SUCCESS] LiveKit SDK is ready!");
                    return true;
                }} else {{
                    console.log("[WAITING] LiveKit SDK not ready yet, checking again...");
                    return false;
                }}
            }}

            // Wait for LiveKit SDK to load
            function waitForLiveKit() {{
                return new Promise((resolve, reject) => {{
                    if (checkLiveKitLoaded()) {{
                        resolve();
                        return;
                    }}

                    let attempts = 0;
                    const maxAttempts = 50; // 5 seconds max

                    const checkInterval = setInterval(() => {{
                        attempts++;
                        if (checkLiveKitLoaded()) {{
                            clearInterval(checkInterval);
                            resolve();
                        }} else if (attempts >= maxAttempts) {{
                            clearInterval(checkInterval);
                            reject(new Error('LiveKit SDK failed to load after ' + maxAttempts + ' attempts'));
                        }}
                    }}, 100);
                }});
            }}
            
            async function getToken() {{
                const payload = {{
                    roomName: roomName,
                    participantName: participantName,
                    customerEmail: customerEmail || null
                }};

                if (currentSessionId) {{
                    payload.sessionId = currentSessionId;
                }}

                const response = await fetch(`${{backendUrl}}/livekit/get-token`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});

                if (!response.ok) {{
                    throw new Error(`Token request failed with status ${{response.status}}`);
                }}

                const data = await response.json();
                return {{ token: data.token, url: data.url, sessionId: data.sessionId }};
            }}
            
            async function connect() {{
                try {{
                    console.log("[CONNECTING] Attempting to connect...");
                    await waitForLiveKit();
                    console.log("[SUCCESS] LiveKit SDK is ready, proceeding with connection...");
                }} catch (error) {{
                    console.error("[ERROR] LiveKit SDK loading failed:", error.message);
                    alert("LiveKit SDK failed to load: " + error.message + ". Please refresh the page.");
                    return;
                }}

                try {{
                    updateStatus("connecting", "● Connecting...");
                    document.getElementById('connectBtn').disabled = true;
                    
                    const {{ token, url, sessionId }} = await getToken();
                    currentSessionId = sessionId || null;
                    lastTranscriptId = null;
                    renderedTranscriptIds.clear();

                    const transcriptContent = document.getElementById('transcriptContent');
                    if (transcriptContent) {{
                        transcriptContent.innerHTML = '';
                    }}
                    updateTranscriptStatus('Connected. Listening for conversation...');
                    startTranscriptPolling();

                    room = new window.LiveKitGlobal.Room({{
                        adaptiveStream: true,
                        dynacast: true,
                    }});

                    // Track when AI starts speaking
                    room.on(window.LiveKitGlobal.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                        console.log("Track subscribed:", track.kind, "from:", participant.identity);
                        if (track.kind === window.LiveKitGlobal.Track.Kind.Audio) {{
                            const audioElement = track.attach();
                            document.body.appendChild(audioElement);
                            
                            // Update status to show AI is speaking
                            updateStatus("active", "Listening...");
                            
                            // Listen for when audio ends
                            audioElement.onended = () => {{
                                console.log("AI finished speaking");
                                updateStatus("connected", "● Ready - Your turn!");
                            }};
                        }}
                    }});
                    
                    // Track when tracks are unmuted (AI starts talking)
                    room.on(window.LiveKitGlobal.RoomEvent.TrackUnmuted, (publication, participant) => {{
                        console.log("Track unmuted:", publication.kind);
                        if (publication.kind === window.LiveKitGlobal.Track.Kind.Audio && participant.identity !== participantName) {{
                            updateStatus("active", "Listening...");
                        }}
                    }});
                    
                    // Track when tracks are muted (AI stops talking)
                    room.on(window.LiveKitGlobal.RoomEvent.TrackMuted, (publication, participant) => {{
                        console.log("Track muted:", publication.kind);
                        if (publication.kind === window.LiveKitGlobal.Track.Kind.Audio && participant.identity !== participantName) {{
                            updateStatus("connected", "● Ready - Your turn!");
                        }}
                    }});
                    
                    room.on(window.LiveKitGlobal.RoomEvent.Disconnected, () => {{
                        handleDisconnect();
                    }});
                    
                    await room.connect(url, token);
                    await room.localParticipant.setMicrophoneEnabled(true);
                    
                    isConnected = true;
                    updateStatus("connected", "● Connected - Ready!");
                    document.getElementById('connectBtn').style.display = 'none';
                    document.getElementById('disconnectBtn').style.display = 'block';
                    document.getElementById('visualizer').classList.add('visible');

                }} catch (error) {{
                    console.error("Failed to connect:", error);
                    alert("Failed to connect: " + error.message);
                    updateStatus("disconnected", "● Disconnected");
                    document.getElementById('connectBtn').disabled = false;
                    stopTranscriptPolling();
                    updateTranscriptStatus('Connection failed');
                }}
            }}
            
            async function disconnect() {{
                if (room) {{
                    room.disconnect();
                    room = null;
                }}
                currentSessionId = null;
                stopTranscriptPolling();
                handleDisconnect();
            }}

            function handleDisconnect() {{
                isConnected = false;
                updateStatus("disconnected", "● Disconnected");
                document.getElementById('connectBtn').style.display = 'block';
                document.getElementById('connectBtn').disabled = false;
                document.getElementById('disconnectBtn').style.display = 'none';
                document.getElementById('visualizer').classList.remove('visible');
                stopTranscriptPolling();
                updateTranscriptStatus('Disconnected');
            }}
            
            function updateStatus(state, message) {{
                const statusEl = document.getElementById('status');
                statusEl.className = 'status ' + state;
                statusEl.textContent = message;
            }}

            function updateTranscriptStatus(message) {{
                const statusEl = document.getElementById('transcriptStatus');
                if (statusEl) {{
                    statusEl.textContent = message;
                }}
            }}

            function stopTranscriptPolling() {{
                if (transcriptInterval) {{
                    clearInterval(transcriptInterval);
                    transcriptInterval = null;
                }}
            }}

            async function fetchTranscriptUpdates() {{
                if (!roomName) {{
                    return;
                }}

                try {{
                    let url = `${{backendUrl}}/livekit/transcript/${{encodeURIComponent(roomName)}}?limit=200`;
                    if (lastTranscriptId !== null) {{
                        url += `&since_id=${{lastTranscriptId}}`;
                    }}

                    const response = await fetch(url);
                    if (!response.ok) {{
                        if (response.status !== 404) {{
                            console.warn('Transcript fetch failed', response.status);
                        }}
                        return;
                    }}

                    const data = await response.json();
                    if (!currentSessionId && data && data.session_id) {{
                        currentSessionId = data.session_id;
                    }}
                    if (data && Array.isArray(data.transcripts)) {{
                        renderTranscripts(data.transcripts);
                    }}
                }} catch (error) {{
                    console.warn('Transcript polling error', error);
                }}
            }}

            function startTranscriptPolling() {{
                stopTranscriptPolling();
                fetchTranscriptUpdates();
                transcriptInterval = setInterval(fetchTranscriptUpdates, 4000);
            }}

            function addTranscriptItem(type, message, timestamp) {{
                const container = document.getElementById('transcriptContent');
                if (!container) {{
                    return;
                }}

                const item = document.createElement('div');
                item.className = `transcript-item ${{type}}`;

                const label = document.createElement('div');
                label.className = 'transcript-label';

                if (type === 'user') {{
                    label.textContent = '👤 You';
                }} else if (type === 'agent') {{
                    label.textContent = '🤖 Alex';
                }} else {{
                    label.textContent = 'ℹ️ System';
                }}

                const textDiv = document.createElement('div');
                textDiv.className = 'transcript-message';
                textDiv.textContent = message;

                item.appendChild(label);
                item.appendChild(textDiv);

                if (timestamp) {{
                    const timeDiv = document.createElement('div');
                    timeDiv.className = 'transcript-time';
                    timeDiv.textContent = new Date(timestamp).toLocaleTimeString();
                    item.appendChild(timeDiv);
                }}

                container.appendChild(item);
                container.scrollTop = container.scrollHeight;
            }}

            function renderTranscripts(entries) {{
                if (!Array.isArray(entries)) {{
                    return;
                }}

                let newMessages = 0;
                entries.forEach(entry => {{
                    if (!entry || renderedTranscriptIds.has(entry.id)) {{
                        return;
                    }}

                    const speakerType = entry.speaker === 'assistant' ? 'agent'
                        : entry.speaker === 'user' ? 'user'
                        : 'system';

                    addTranscriptItem(speakerType, entry.text, entry.created_at);
                    renderedTranscriptIds.add(entry.id);
                    lastTranscriptId = entry.id;
                    newMessages += 1;
                }});

                if (newMessages > 0) {{
                    updateTranscriptStatus('Transcript updated just now');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    # Format the HTML with the actual values
    try:
        livekit_html_formatted = livekit_html.format(
            room_name=room_name,
            participant_name=participant_name,
            backend_url_json=json.dumps(BACKEND_URL),
            customer_email_json=json.dumps(customer_email)
        )
    except KeyError as e:
        st.error(f"Error formatting template: {str(e)}")
        return

    # Render the HTML using components.html for full interactivity
    components.html(livekit_html_formatted, height=700, scrolling=True)
    
    # Additional info
    st.info("""
    **💡 Note:** Voice Chat uses real-time AI conversation powered by OpenAI's Realtime API.
    The AI travel consultant can understand natural speech and respond immediately.
    """)


def show_dashboard_overview(email):
    """Show advanced dashboard overview with charts and analytics"""
    
    # Modern dashboard header
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 8px; margin-bottom: 1rem; 
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
            <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 600; text-align: center;">
                Travel Analytics Dashboard
            </h1>
            <p style="color: rgba(255,255,255,0.9); margin: 0.3rem 0 0 0; text-align: center; font-size: 0.9rem;">
                Comprehensive travel insights and booking analytics
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get stats and booking data
    stats = get_dashboard_stats(email)
    bookings_data = get_booking_analytics(email)
    
    # Key Metrics Row - Enhanced with icons and trends
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 0.8rem; border-radius: 8px; text-align: center; 
                        box-shadow: 0 3px 10px rgba(102, 126, 234, 0.15); margin-bottom: 0.5rem;">
                <h3 style="color: white; margin: 0; font-size: 0.8rem; opacity: 0.9;">Total Bookings</h3>
                <h2 style="color: white; margin: 0.3rem 0; font-size: 1.8rem; font-weight: 600;">{stats['total_bookings']}</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.7rem;">All time bookings</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 0.8rem; border-radius: 8px; text-align: center; 
                        box-shadow: 0 3px 10px rgba(240, 147, 251, 0.15); margin-bottom: 0.5rem;">
                <h3 style="color: white; margin: 0; font-size: 0.8rem; opacity: 0.9;">Cancelled</h3>
                <h2 style="color: white; margin: 0.3rem 0; font-size: 1.8rem; font-weight: 600;">{stats['cancelled_bookings']}</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.7rem;">Cancelled bookings</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 0.8rem; border-radius: 8px; text-align: center; 
                        box-shadow: 0 3px 10px rgba(79, 172, 254, 0.15); margin-bottom: 0.5rem;">
                <h3 style="color: white; margin: 0; font-size: 0.8rem; opacity: 0.9;">Total Spent</h3>
                <h2 style="color: white; margin: 0.3rem 0; font-size: 1.8rem; font-weight: 600;">₹{stats['total_spent']:,.0f}</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.7rem;">Lifetime spending</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 0.8rem; border-radius: 8px; text-align: center; 
                        box-shadow: 0 3px 10px rgba(250, 112, 154, 0.15); margin-bottom: 0.5rem;">
                <h3 style="color: white; margin: 0; font-size: 0.8rem; opacity: 0.9;">Upcoming</h3>
                <h2 style="color: white; margin: 0.3rem 0; font-size: 1.8rem; font-weight: 600;">{stats['upcoming_trips']}</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.7rem;">Future trips</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        # Booking Status Pie Chart
        st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 8px; 
                        box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 0.5rem;">
                <h3 style="color: #333; margin-top: 0; font-size: 1rem; font-weight: 600;">Booking Status Distribution</h3>
        """, unsafe_allow_html=True)
        
        # Create pie chart data
        status_data = bookings_data.get('status_distribution', {})
        if status_data and PLOTLY_AVAILABLE:
            fig_pie = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                color_discrete_sequence=['#667eea', '#f093fb', '#4facfe', '#fa709a'],
                hole=0.4
            )
            fig_pie.update_layout(
                showlegend=True,
                height=250,
                font=dict(size=10),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        elif status_data:
            # Fallback: Show status data as text
            st.markdown("**Booking Status Distribution:**")
            for status, count in status_data.items():
                percentage = (count / sum(status_data.values())) * 100
                st.markdown(f"• {status.title()}: {count} bookings ({percentage:.1f}%)")
        else:
            st.info("No booking data available for chart")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Monthly Spending Trend
        st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 8px; 
                        box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 0.5rem;">
                <h3 style="color: #333; margin-top: 0; font-size: 1rem; font-weight: 600;">Monthly Spending Trend</h3>
        """, unsafe_allow_html=True)
        
        # Create spending trend chart
        spending_data = bookings_data.get('monthly_spending', [])
        if spending_data and PLOTLY_AVAILABLE:
            df_spending = pd.DataFrame(spending_data)
            fig_line = px.line(
                df_spending, 
                x='month', 
                y='amount',
                markers=True,
                color_discrete_sequence=['#667eea']
            )
            fig_line.update_layout(
                height=250,
                font=dict(size=10),
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Month",
                yaxis_title="Amount (₹)"
            )
            fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_line, use_container_width=True)
        elif spending_data:
            # Fallback: Show spending data as text
            st.markdown("**Monthly Spending:**")
            for month_data in spending_data:
                st.markdown(f"• {month_data['month']}: ₹{month_data['amount']:,.0f}")
        else:
            # Generate sample data for demo
            if PLOTLY_AVAILABLE:
                months = pd.date_range(start='2024-01-01', periods=6, freq='M').strftime('%b %Y')
                amounts = np.random.randint(200, 800, 6).tolist()
                df_demo = pd.DataFrame({'month': months, 'amount': amounts})
                
                fig_line = px.line(
                    df_demo, 
                    x='month', 
                    y='amount',
                    markers=True,
                    color_discrete_sequence=['#667eea']
                )
                fig_line.update_layout(
                    height=250,
                    font=dict(size=10),
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis_title="Month",
                    yaxis_title="Amount (₹)"
                )
                fig_line.update_traces(line=dict(width=3), marker=dict(size=8))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No spending data available")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Analytics Summary Row
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Destinations
        st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 8px; 
                        box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 0.5rem;">
                <h3 style="color: #333; margin-top: 0; font-size: 1rem; font-weight: 600;">Top Destinations</h3>
        """, unsafe_allow_html=True)
        
        destinations = bookings_data.get('top_destinations', [])
        if destinations:
            for i, dest in enumerate(destinations[:5], 1):
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                padding: 0.5rem; margin: 0.3rem 0; background: #f8f9ff; 
                                border-radius: 6px; border-left: 3px solid #667eea;">
                        <span style="font-weight: 600; color: #333; font-size: 0.9rem;">#{i} {dest['destination']}</span>
                        <span style="color: #667eea; font-weight: 600; font-size: 0.8rem;">{dest['count']} trips</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No destination data available")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # Travel Insights
        st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 8px; 
                        box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 0.5rem;">
                <h3 style="color: #333; margin-top: 0; font-size: 1rem; font-weight: 600;">Travel Insights</h3>
        """, unsafe_allow_html=True)
        
        # Calculate insights
        avg_booking_value = stats['total_spent'] / max(stats['total_bookings'], 1)
        success_rate = ((stats['total_bookings'] - stats['cancelled_bookings']) / max(stats['total_bookings'], 1)) * 100
        
        insights = [
            f"Average booking value: ₹{avg_booking_value:.0f}",
            f"Success rate: {success_rate:.1f}%",
            f"Bookings this year: {stats['total_bookings']}",
            f"Favorite service: Travel Package" if stats['total_bookings'] > 0 else "No bookings yet"
        ]
        
        for insight in insights:
            st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.3rem 0; background: #f0f8ff; 
                            border-radius: 6px; border-left: 3px solid #4facfe;">
                    <span style="font-size: 0.85rem; color: #333;">{insight}</span>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Recent Activity Timeline
    st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; 
                    box-shadow: 0 3px 10px rgba(0,0,0,0.05); margin-bottom: 0.5rem;">
            <h3 style="color: #333; margin-top: 0; font-size: 1rem; font-weight: 600;">Recent Activity</h3>
    """, unsafe_allow_html=True)
    
    recent_bookings = bookings_data.get('recent_bookings', [])
    if recent_bookings:
        for booking in recent_bookings[:3]:
            status_color = "#4caf50" if booking['status'] == 'confirmed' else "#ff9800" if booking['status'] == 'pending' else "#f44336"
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 0.6rem; margin: 0.3rem 0; 
                            background: #fafafa; border-radius: 6px; border-left: 3px solid {status_color};">
                    <div style="flex: 1;">
                        <strong style="color: #333; font-size: 0.9rem;">{booking['service_type']}</strong><br>
                        <span style="color: #666; font-size: 0.8rem;">{booking['destination']} • {booking['departure_date']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: {status_color}; font-weight: 600; text-transform: uppercase; font-size: 0.8rem;">{booking['status']}</span><br>
                        <span style="color: #667eea; font-weight: 600; font-size: 0.9rem;">₹{booking['amount']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent bookings to display")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    # Check for password reset parameters first
    reset_token, reset_email = check_reset_params()
    if reset_token and reset_email:
        show_password_reset_form(reset_token, reset_email)
        return
    
    # Initialize session state
    if 'customer_email' not in st.session_state:
        st.session_state.customer_email = None
    if 'customer_name' not in st.session_state:
        st.session_state.customer_name = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'backend_checked' not in st.session_state:
        st.session_state.backend_checked = False
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'dashboard'  # Default to dashboard on first load
    
    # Check backend status on first load
    if not st.session_state.backend_checked:
        st.session_state.backend_status = check_backend_status()
        st.session_state.backend_checked = True
    
    # Show login if not logged in (no sidebar)
    if not st.session_state.get('logged_in') or not st.session_state.get('customer_email'):
        # Show login screen without sidebar
        login_screen()
        return
    
    # Only show sidebar and main app after successful login
    # Show sidebar after login
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            display: block !important;
        }
        .main .block-container {
            max-width: calc(100% - 300px) !important;
            margin-left: 300px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Import and use the sidebar component
    try:
        from sidebar_buttons import create_sidebar_navigation
        create_sidebar_navigation()
    except ImportError:
        # Fallback to original sidebar
        sidebar_navigation()
    
    # Check current view
    current_view = st.session_state.get('current_view', 'conversation')
    show_bookings = st.session_state.get('show_bookings', False)
    show_chat_history = st.session_state.get('show_chat_history', False)
    
    # Main container wrapper
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Route to appropriate view
    if current_view == 'dashboard':
        # Stop any audio/conversation when viewing dashboard
        if st.session_state.get('conversation_running', False):
            print("🛑 Auto-stopping conversation - viewing dashboard")
            stop_audio()
            st.session_state.conversation_running = False
        # Show dashboard
        email = st.session_state.get('customer_email')
        show_dashboard_overview(email)
        return
    
    # Show Voice Chat view (NEW LiveKit Integration)
    if current_view == 'voice_chat':
        # Stop any audio/conversation when entering voice chat
        if st.session_state.get('conversation_running', False):
            print("🛑 Auto-stopping Azure conversation - switching to LiveKit")
            stop_audio()
            st.session_state.conversation_running = False
        show_voice_chat_interface()
        return
    
    # Show My Bookings view
    if show_bookings:
        # Stop any audio/conversation when viewing bookings
        if st.session_state.get('conversation_running', False):
            print("🛑 Auto-stopping conversation - viewing bookings")
            stop_audio()
            st.session_state.conversation_running = False
        st.markdown("### 📋 My Bookings")
        email = st.session_state.get('customer_email')
        if email:
            try:
                response = requests.get(f"{BACKEND_URL}/my_bookings/{email}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    bookings = data.get('bookings', [])
                    
                    if bookings and isinstance(bookings, list) and len(bookings) > 0:
                        logger.info(f"✅ Found {len(bookings)} booking(s) for user: {email}")
                        print(f"✅ INFO: Found {len(bookings)} booking(s) for user: {email}")
                        st.success(f"Found {len(bookings)} booking(s) for {email}")
                        
                        for i, booking in enumerate(bookings, 1):
                            if isinstance(booking, dict):
                                # Create booking details section
                                booking_id = booking.get('booking_id', i)
                                service_details = booking.get('service_details', '')
                                special_requests = booking.get('special_requests', '')
                                
                                # Build HTML content properly
                                html_content = f"""
                                    <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #667eea; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <h3 style="color: #667eea; margin-top: 0;">✈️ Booking #{booking_id}</h3>
                                        <p style="margin: 0.5rem 0; font-size: 1.1rem;"><strong>📧 Customer Email:</strong> {email}</p>
                                        <p style="margin: 0.5rem 0; font-size: 1.1rem;"><strong>🎯 Service Type:</strong> {booking.get('service_type', 'Travel Service')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>🌍 Destination:</strong> {booking.get('destination', 'Saudi Arabia')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>📅 Departure Date:</strong> {booking.get('departure_date', 'N/A')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>📅 Return Date:</strong> {booking.get('return_date', 'N/A')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>👥 Number of Travelers:</strong> {booking.get('num_travelers', 1)}</p>
                                """
                                
                                # Add service details if available
                                if service_details:
                                    html_content += f'<p style="margin: 0.5rem 0;"><strong>📋 Service Details:</strong> {service_details}</p>'
                                
                                # Add special requests if available
                                if special_requests:
                                    html_content += f'<p style="margin: 0.5rem 0;"><strong>💬 Special Requests:</strong> {special_requests}</p>'
                                
                                # Complete the HTML
                                html_content += f"""
                                        <p style="margin: 0.5rem 0; font-size: 1.2rem; color: #667eea;"><strong>💰 Total Amount:</strong> ₹{booking.get('total_amount', 0)}</p>
                                        <p style="margin: 0.5rem 0;"><strong>📊 Status:</strong> <span style="color: green; font-weight: bold;">{booking.get('status', 'pending').upper()}</span></p>
                                        <p style="font-size: 0.85rem; color: #666; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 0.5rem;">📅 Booked on: {booking.get('created_at', 'N/A')}</p>
                                    </div>
                                """
                                
                                st.markdown(html_content, unsafe_allow_html=True)
                                
                                # Add action buttons for each booking
                                col1, col2, col3 = st.columns([1, 1, 2])
                                with col1:
                                    if st.button(f"🗑️ Cancel", key=f"cancel_{booking_id}", help="Cancel this booking"):
                                        try:
                                            response = requests.post(f"{BACKEND_URL}/cancel_booking", 
                                                                   json={"booking_id": booking_id, "customer_email": email}, 
                                                                   timeout=10)
                                            if response.status_code == 200:
                                                st.success("✅ Booking cancelled successfully!")
                                                st.rerun()
                                            else:
                                                st.error("❌ Failed to cancel booking")
                                        except Exception as e:
                                            st.error(f"❌ Error cancelling booking: {str(e)}")
                                
                                with col2:
                                    if st.button(f"📅 Reschedule", key=f"reschedule_{booking_id}", help="Reschedule this booking"):
                                        st.session_state[f"show_reschedule_{booking_id}"] = True
                                        st.rerun()
                                
                                # Show reschedule form if requested
                                if st.session_state.get(f"show_reschedule_{booking_id}", False):
                                    with st.container():
                                        st.markdown("---")
                                        st.markdown("### 📅 Reschedule Booking")
                                        with st.form(f"reschedule_form_{booking_id}"):
                                            new_departure = st.date_input("New Departure Date", 
                                                                         value=datetime.strptime(booking.get('departure_date', '2025-12-15'), '%Y-%m-%d').date(),
                                                                         key=f"new_dep_{booking_id}")
                                            new_return = st.date_input("New Return Date (if applicable)", 
                                                                      value=datetime.strptime(booking.get('return_date', '2025-12-20'), '%Y-%m-%d').date() if booking.get('return_date') else None,
                                                                      key=f"new_ret_{booking_id}")
                                            
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.form_submit_button("✅ Confirm Reschedule"):
                                                    try:
                                                        response = requests.post(f"{BACKEND_URL}/reschedule_booking", 
                                                                               json={"booking_id": booking_id, 
                                                                                     "customer_email": email,
                                                                                     "new_departure_date": new_departure.strftime('%Y-%m-%d'),
                                                                                     "new_return_date": new_return.strftime('%Y-%m-%d') if new_return else None}, 
                                                                               timeout=10)
                                                        if response.status_code == 200:
                                                            st.success("✅ Booking rescheduled successfully!")
                                                            st.session_state[f"show_reschedule_{booking_id}"] = False
                                                            st.rerun()
                                                        else:
                                                            st.error("❌ Failed to reschedule booking")
                                                    except Exception as e:
                                                        st.error(f"❌ Error rescheduling booking: {str(e)}")
                                            
                                            with col2:
                                                if st.form_submit_button("❌ Cancel"):
                                                    st.session_state[f"show_reschedule_{booking_id}"] = False
                                                    st.rerun()
                                        
                                        st.markdown("---")
                        
                    else:
                        # No bookings found - show friendly message
                        logger.info(f"📋 No bookings found for user: {email}")
                        print(f"📋 INFO: No bookings found for user: {email}")
                        st.markdown("""
                            <div style="text-align: center; padding: 3rem 2rem; background: rgba(255,255,255,0.05); border-radius: 12px; margin: 2rem 0;">
                                <div style="font-size: 4rem; margin-bottom: 1rem;">📋</div>
                                <h3 style="color: white; margin-bottom: 1rem;">No Bookings Yet</h3>
                                <p style="color: rgba(255,255,255,0.8); margin-bottom: 1.5rem; font-size: 1.1rem;">
                                    You haven't made any travel bookings yet. Start a conversation with Alex to plan your next adventure!
                                </p>
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">
                                        <strong>💡 Tip:</strong> Ask Alex about destinations, flights, hotels, or travel packages to get started!
                                    </p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"Failed to load bookings (Status: {response.status_code})")
            except Exception as e:
                st.error(f"Error loading bookings: {e}")
        return
    
    # Show Chat History view
    if show_chat_history:
        # Stop any audio/conversation when viewing chat history
        if st.session_state.get('conversation_running', False):
            print("🛑 Auto-stopping conversation - viewing chat history")
            stop_audio()
            st.session_state.conversation_running = False
        st.markdown("### 💭 Chat History")
        email = st.session_state.get('customer_email')
        if email:
            try:
                response = requests.get(f"{BACKEND_URL}/chat_history/{email}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    conversations = data.get('conversations', [])
                    count = data.get('count', 0)
                    
                    if conversations and len(conversations) > 0:
                        logger.info(f"✅ Found {len(conversations)} chat conversation(s) for user: {email}")
                        print(f"✅ INFO: Found {len(conversations)} chat conversation(s) for user: {email}")
                        st.success(f"Found {len(conversations)} conversation(s) for {email}")
                        
                        for i, chat in enumerate(conversations, 1):
                            if isinstance(chat, dict):
                                st.markdown(f"""
                                    <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #4caf50; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                                        <h3 style="color: #4caf50; margin-top: 0;">💬 Conversation #{i}</h3>
                                        <p style="margin: 0.5rem 0;"><strong>📅 Date:</strong> {chat.get('created_at', 'N/A')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>💬 User Message:</strong> {chat.get('user_message', 'N/A')}</p>
                                        <p style="margin: 0.5rem 0;"><strong>🤖 Alex Response:</strong> {chat.get('ai_response', 'N/A')}</p>
                                        <p style="font-size: 0.85rem; color: #666; margin-top: 1rem; border-top: 1px solid #eee; padding-top: 0.5rem;">🕒 Duration: {chat.get('duration', 'N/A')}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        # No chat history found - show friendly message
                        logger.info(f"💭 No chat history found for user: {email}")
                        print(f"💭 INFO: No chat history found for user: {email}")
                        st.markdown("""
                            <div style="text-align: center; padding: 3rem 2rem; background: rgba(255,255,255,0.05); border-radius: 12px; margin: 2rem 0;">
                                <div style="font-size: 4rem; margin-bottom: 1rem;">💭</div>
                                <h3 style="color: white; margin-bottom: 1rem;">No Chat History Yet</h3>
                                <p style="color: rgba(255,255,255,0.8); margin-bottom: 1.5rem; font-size: 1.1rem;">
                                    You haven't had any conversations with Alex yet. Start chatting to see your conversation history here!
                                </p>
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">
                                        <strong>💡 Tip:</strong> Click "New Conversation" to start chatting with Alex about your travel plans!
                                    </p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"Failed to load chat history (Status: {response.status_code})")
            except Exception as e:
                st.error(f"Error loading chat history: {e}")
        return
    
    # Default conversation view
    # Header
    customer_name = st.session_state.get('customer_name', 'Guest')
    customer_email = st.session_state.get('customer_email', 'No email')
    st.markdown(f"""
        <div class="header">
            <h1>Attar Travel</h1>
            <p>Alex - Saudi Arabia Travel Specialist AI Agent | Logged in as: {customer_name} ({customer_email})</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"guest_{os.urandom(8).hex()}"
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        # Load previous conversations from database when first initializing
        email = st.session_state.get('customer_email')
        if email:
            try:
                print(f"🔄 Auto-loading chat history for: {email}")
                response = requests.get(f"{BACKEND_URL}/chat_history/{email}", timeout=10)
                print(f"📡 Backend response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    conversations = data.get('conversations', [])
                    print(f"📊 Found {len(conversations)} conversations in database")
                    
                    if conversations and len(conversations) > 0:
                        for idx, conv in enumerate(conversations):
                            # Extract timestamp
                            created_at = conv.get('created_at', '')
                            time_str = ''
                            if created_at:
                                try:
                                    if ' ' in created_at:
                                        time_str = created_at.split(' ')[1][:5]
                                    else:
                                        time_str = created_at[:5]
                                except:
                                    time_str = created_at[:16] if len(created_at) >= 16 else created_at
                            
                            # Add user message
                            user_msg = conv.get('user_message', '')
                            if user_msg:
                                st.session_state.chat_history.append({
                                    'role': 'User',
                                    'text': user_msg,
                                    'time': time_str
                                })
                            
                            # Add AI response
                            ai_msg = conv.get('ai_response', '')
                            if ai_msg:
                                st.session_state.chat_history.append({
                                    'role': 'Alex',
                                    'text': ai_msg,
                                    'time': time_str
                                })
                        
                        print(f"✅ Auto-loaded {len(st.session_state.chat_history)} messages on initialization")
                    else:
                        print("⚠️ No conversations found in database")
            except Exception as e:
                print(f"❌ Could not load chat history on init: {str(e)}")
                import traceback
                traceback.print_exc()
    if 'conversation_running' not in st.session_state:
        st.session_state.conversation_running = False
    if 'turn_number' not in st.session_state:
        st.session_state.turn_number = 0
    # Don't automatically play welcome on first load - only when New Chat is clicked
    
    # Chat display
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        if msg['role'] == 'Alex':
            st.markdown(f"""
                <div class="message-emma">
                    <div class="bubble-emma">
                        <div class="sender-name">Alex</div>
                        <p class="message-text">{msg['text']}</p>
                        <div class="message-time">{msg.get('time', '')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="message-user">
                    <div class="bubble-user">
                        <p class="message-text">{msg['text']}</p>
                        <div class="message-time">{msg.get('time', '')}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle welcome greeting when New Chat is clicked
    if st.session_state.get('play_welcome_on_new_chat', False):
        st.session_state.play_welcome_on_new_chat = False  # Reset the flag
        
        # Get and play welcome message
        try:
            response = requests.get(f"{BACKEND_URL}/welcome", timeout=10)
            if response.status_code == 200:
                data = response.json()
                welcome_text = data.get('message', 'Hello! I am Alex, your Saudi Arabia Travel Specialist. How can I help you plan your next adventure?')
                welcome_audio = data.get('audio_base64')
                
                # Add welcome message to chat history
                current_time = datetime.now().strftime('%H:%M')
                st.session_state.chat_history.append({
                    'role': 'Alex',
                    'text': welcome_text,
                    'time': current_time
                })
                
                # Play welcome audio if available (without interruption for full message)
                if welcome_audio:
                    st.markdown('<div class="status-box speaking">Alex is speaking...</div>', unsafe_allow_html=True)
                    audio_bytes = base64.b64decode(welcome_audio)
                    
                    # Play audio automatically without interruption detection
                    play_audio(audio_bytes, check_interruption=False)
                
                st.rerun()  # Refresh to show the welcome message
        except Exception as e:
            st.error(f"Error playing welcome message: {e}")
    
    # Show bookings if requested
    if st.session_state.get('show_bookings', False):
        show_my_bookings()
    
    # Show chat history if requested - this is handled in the main view routing above
    # Removed duplicate chat history handling
    
    # Initialize mute state
    if 'audio_muted' not in st.session_state:
        st.session_state.audio_muted = False
    
    # Audio Control Buttons Container (bottom right corner)
    st.markdown("""
        <style>
        .audio-controls-container {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 15px !important;
            z-index: 1000 !important;
        }
        
        /* Style the buttons in the right column to look like the audio control buttons */
        .audio-controls-container .stButton > button {
            width: 60px !important;
            height: 60px !important;
            border-radius: 12px !important;
            border: none !important;
            color: white !important;
            font-size: 1.8rem !important;
            cursor: pointer !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
            margin-bottom: 10px !important;
        }
        
        .audio-controls-container .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
        }
        
        .audio-controls-container .stButton > button:active {
            transform: translateY(0px) !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Mute button styling */
        [data-testid="stButton"]:has([data-testid="baseButton-secondary"][aria-label*="mute_button"]) > button,
        button[data-testid="baseButton-secondary"][aria-label*="mute_button"] {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
        }
        
        /* Start/Stop button styling */
        [data-testid="stButton"]:has([data-testid="baseButton-secondary"][aria-label*="conversation"]) > button,
        button[data-testid="baseButton-secondary"][aria-label*="conversation"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        
        /* Alternative approach - target buttons by their position in the container */
        .audio-controls-container .stButton:first-of-type > button {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%) !important;
        }
        
        .audio-controls-container .stButton:last-of-type > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create audio control buttons container (bottom right corner)
    st.markdown("""
        <div class="audio-controls-container">
    """, unsafe_allow_html=True)
    
    # Create two columns to position buttons in bottom right
    col1, col2 = st.columns([9, 1])
    
    with col2:
        # Stack buttons vertically in bottom right corner
        # Mute/Unmute Button (Microphone icon) - Top button
        mute_icon = "🎤"  # Microphone icon like in the reference image
        
        if st.button(mute_icon, key="mute_button", help="Mute/Unmute Audio"):
            st.session_state.audio_muted = not st.session_state.audio_muted
            if st.session_state.audio_muted:
                stop_audio()
            st.rerun()
        
        # Start/Stop Conversation Button - Bottom button
        start_icon = "⏹️" if st.session_state.conversation_running else "🎙️"  # Microphone with sound waves
        
        if st.session_state.conversation_running:
            if st.button(start_icon, key="stop_conversation_btn", help="Stop Conversation"):
                st.session_state.conversation_running = False
                st.rerun()
        else:
            if st.button(start_icon, key="start_conversation_btn", help="Start Audio Conversation"):
                st.session_state.conversation_running = True
                st.session_state.turn_number = 0
                st.session_state.play_welcome_on_start = True  # Flag to play welcome when conversation starts
                st.rerun()
    
    st.markdown("""
        </div>
    """, unsafe_allow_html=True)
    
    
    # Voice-to-voice conversation interface
    # Only run voice conversation when in "New Chat" view (conversation view)
    if st.session_state.conversation_running and st.session_state.get('current_view') == 'conversation':
        # Check if conversation was stopped or view changed
        if not st.session_state.get('conversation_running', False) or st.session_state.get('current_view') != 'conversation':
            print("🛑 Stopping voice conversation - conversation stopped or view changed")
            stop_audio()
            st.session_state.conversation_running = False
            st.rerun()
            return
        
        # Play welcome greeting when conversation first starts
        if st.session_state.get('play_welcome_on_start', False):
            st.session_state.play_welcome_on_start = False  # Reset the flag
            
            # Get and play welcome message
            try:
                response = requests.get(f"{BACKEND_URL}/welcome", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    welcome_text = data.get('message', 'Hello! I am Alex, your Saudi Arabia Travel Specialist. How can I help you plan your next adventure?')
                    welcome_audio = data.get('audio_base64')
                    
                    # Add welcome message to chat history
                    current_time = datetime.now().strftime('%H:%M')
                    st.session_state.chat_history.append({
                        'role': 'Alex',
                        'text': welcome_text,
                        'time': current_time
                    })
                    
                    # Play welcome audio if available (without interruption for full message)
                    if welcome_audio:
                        audio_bytes = base64.b64decode(welcome_audio)
                        play_audio(audio_bytes, check_interruption=False)
                    
                    st.rerun()  # Refresh to show the welcome message
            except Exception as e:
                st.error(f"Error playing welcome message: {e}")
        
        st.markdown('<div class="status-box listening">LISTENING... Speak now!</div>', unsafe_allow_html=True)
        
        # Record user
        audio_path = record_audio(duration=8)
        
        if audio_path:
            st.markdown('<div class="status-box processing">Processing...</div>', unsafe_allow_html=True)
            
            # Transcribe
            user_text = transcribe(audio_path)
            os.unlink(audio_path)
            
            if user_text:
                # Get AI response
                response_text, audio_base64 = get_ai_response(user_text, st.session_state.session_id, st.session_state.customer_email)
                
                if response_text:
                    current_time = datetime.now().strftime('%H:%M')
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        'role': 'User',
                        'text': user_text,
                        'time': current_time
                    })
                    st.session_state.chat_history.append({
                        'role': 'Alex',
                        'text': response_text,
                        'time': current_time
                    })
                    
                    # Play Alex's response with interruption detection
                    if audio_base64:
                        st.markdown('<div class="status-box speaking">Alex is speaking... (speak to interrupt)</div>', unsafe_allow_html=True)
                        audio_bytes = base64.b64decode(audio_base64)
                        playback_completed = play_audio(audio_bytes, check_interruption=True)
                        
                        # If user interrupted, show notification
                        if not playback_completed:
                            print("🔄 User interrupted AI - starting immediate recording")
                            st.session_state.turn_number += 1
                            # Immediately continue to next iteration to record user
                            st.rerun()
                            return
                    
                    st.session_state.turn_number += 1
                    
                    # Check if conversation is still running before continuing
                    if not st.session_state.get('conversation_running', False):
                        stop_audio()
                        st.rerun()
                        return
                    
                    # IMPORTANT: Continue listening automatically (like travel_realtime1.py)
                    time.sleep(1)  # Small pause before next turn
                    st.rerun()
                else:
                    # AI response failed, continue listening
                    time.sleep(0.5)
                    st.rerun()
            else:
                # No transcription, continue listening
                time.sleep(0.5)
                st.rerun()
        else:
            # No audio recorded, continue listening
            time.sleep(0.5)
            st.rerun()
    
    # Close main container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

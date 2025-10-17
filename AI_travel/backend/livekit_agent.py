"""
LiveKit Voice Agent with OpenAI Realtime API
Real-time voice conversation agent that joins LiveKit rooms
Integrated with Attar Travel AI system
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import aiohttp
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import openai, silero
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AttarTravelVoiceAssistant:
    """Real-time voice assistant using OpenAI Realtime API for Attar Travel"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        logger.info("🤖 Attar Travel Voice Assistant initialized")
        self.backend_url = self._resolve_backend_url()

    def _resolve_backend_url(self) -> str:
        for env_key in ("TRAVEL_BACKEND_URL", "BACKEND_API_URL", "BACKEND_URL"):
            value = os.getenv(env_key)
            if value:
                return value.rstrip('/')
        return "http://localhost:8000"

    async def _fetch_session_info(self, room_name: str) -> Optional[Dict[str, Any]]:
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
                            "⚠️ LiveKit session info request failed (%s): HTTP %s",
                            room_name,
                            resp.status
                        )
        except Exception as error:
            logger.warning(f"⚠️ Could not fetch session info for {room_name}: {error}")

        return None

    def _extract_text(self, message: Any) -> Optional[str]:
        if message is None:
            return None

        if isinstance(message, str):
            return message.strip() or None

        content = getattr(message, "content", None)
        if isinstance(content, str):
            content = content.strip()
            if content:
                return content

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
        if not self.backend_url:
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
                            "⚠️ Transcript save failed (%s): %s",
                            resp.status,
                            error_text
                        )
                    else:
                        data = await resp.json()
                        if isinstance(data, dict):
                            context["session_id"] = data.get("session_id", context.get("session_id"))
                            context["customer_email"] = data.get("customer_email", context.get("customer_email"))
        except Exception as error:
            logger.warning(f"⚠️ Unable to send transcript: {error}")
    
    async def entrypoint(self, ctx: JobContext):
        """
        Main entry point when agent joins a LiveKit room
        This is called automatically when a room session starts
        """
        logger.info(f"🚀 Agent joining room: {ctx.room.name}")
        
        # Connect to the room
        await ctx.connect()
        logger.info(f"✅ Agent connected to room: {ctx.room.name}")

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
        
        # System instructions for the assistant
        initial_instructions = (
            "You are Alex, a patient, friendly, and knowledgeable travel consultant for Attar Travel, "
            "specializing in Saudi Arabia travel. Your goal is to provide exceptional customer service "
            "with warmth, patience, and helpful guidance.\n"
            "\n"
            "IMPORTANT - FIRST MESSAGE:\n"
            "When a user first connects to the voice chat, ALWAYS greet them warmly. Say something like:\n"
            "'Hello! I'm Alex from Attar Travel. How can I help you plan your perfect journey to Saudi Arabia today?'\n"
            "or 'Hi there! Welcome to Attar Travel. I'm Alex, your travel consultant. What can I help you with?'\n"
            "Keep the greeting natural, warm, and brief!\n"
            "\n"
            "YOUR EXPERTISE:\n"
            "- Umrah and Hajj pilgrimage packages with complete guidance\n"
            "- Tourist destinations: Riyadh, Jeddah, Mecca, Medina, AlUla, Red Sea, Taif, Abha, NEOM\n"
            "- Hotel bookings, flight arrangements, visa processing\n"
            "- Cultural insights, Islamic heritage sites, local customs\n"
            "- Real-time travel information, weather, best visiting times\n"
            "- Group tours, family packages, honeymoon trips, business travel\n"
            "- Saudi cuisine, shopping, entertainment, adventure activities\n"
            "\n"
            "COMMUNICATION STYLE - BE VERY NATURAL:\n"
            "✓ Be PATIENT - Take your time to understand what the customer wants\n"
            "✓ Be OBEDIENT - Always ready to help with any query about Saudi Arabia\n"
            "✓ Be CONVERSATIONAL - Respond naturally to customer reactions:\n"
            "  • When customer says 'Thank you' → Reply warmly: 'You're welcome! Happy to help!'\n"
            "  • When customer says 'Great/Wonderful' → Acknowledge: 'I'm glad you like it!'\n"
            "  • When customer asks 'When...' → Provide specific timing/season details\n"
            "  • When customer asks 'Which...' → Give clear recommendations with reasons\n"
            "  • When customer asks 'Where...' → Describe locations with helpful details\n"
            "  • When customer asks 'How much...' → Provide approximate costs and packages\n"
            "\n"
            "✓ Use SHORT sentences - Perfect for voice conversation\n"
            "✓ Be ENTHUSIASTIC - Show genuine excitement about Saudi Arabia\n"
            "✓ Be HELPFUL - Proactively offer additional information\n"
            "✓ Be RESPECTFUL - Honor religious and cultural sensitivities\n"
            "✓ Be INFORMATIVE - Share interesting facts and tips\n"
            "\n"
            "RESPONSE EXAMPLES:\n"
            "- Customer: 'Tell me about Mecca' → You: 'Mecca is Islam's holiest city! Home to the Sacred Mosque '\n"
            "  'and the Kaaba. Millions visit for Umrah and Hajj. Would you like to know about packages?'\n"
            "- Customer: 'Thank you!' → You: 'You're very welcome! Is there anything else about Saudi Arabia '\n"
            "  'you'd like to know?'\n"
            "- Customer: 'When should I visit?' → You: 'Great question! November to February is perfect - '\n"
            "  'pleasant weather, around 20-25°C. Would you like me to suggest a package?'\n"
            "\n"
            "Always be ready to answer ANY question about Saudi Arabia - from tourist spots to practical travel tips. "
            "Make customers feel valued, heard, and excited about their Saudi journey!\n"
            "\n"
            "HANDLING INTERRUPTIONS:\n"
            "✓ If the customer interrupts you while speaking, STOP immediately and LISTEN\n"
            "✓ Don't be offended - interruptions are natural in conversation\n"
            "✓ After listening, acknowledge what they said and continue helpfully\n"
            "✓ Example: If interrupted, then respond: 'Oh yes, let me address that...'\n"
            "✓ Be flexible and adapt to the customer's pace of conversation\n"
            "✓ This shows respect and creates natural, comfortable dialogue"
        )
        
        # Create the OpenAI Realtime model
        model = openai.realtime.RealtimeModel(
            voice="alloy",  # OpenAI TTS voice: alloy, echo, fable, onyx, nova, shimmer
            temperature=0.8,
            modalities=["text", "audio"],
        )
        
        # Create the agent with instructions and the model
        agent = Agent(
            instructions=initial_instructions,
            llm=model
        )
        
        # Create agent session with interruption handling enabled
        session = AgentSession(
            allow_interruptions=True,  # Allow user to interrupt AI at any time
            min_interruption_duration=0.3,  # Detect interruption after 0.3 seconds of user speech
            min_endpointing_delay=0.4,  # Wait 0.4s after user stops before AI responds
            max_endpointing_delay=5.0,  # Maximum wait time before considering turn complete
        )
        
        # Set up event handlers for real-time streaming feedback
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
        def on_user_speech_started():
            logger.info("👂 User started speaking...")

        @session.on("user_speech_committed")
        def on_user_speech_committed(message):
            logger.info(f"👤 User said: {message.content if hasattr(message, 'content') else message}")
            _queue_transcript("user", message)

        @session.on("agent_speech_started")
        def on_agent_speech_started():
            logger.info("🗣️ Agent started speaking...")

        @session.on("agent_speech_committed")
        def on_agent_speech_committed(message):
            logger.info(f"🤖 Agent said: {message.content if hasattr(message, 'content') else message}")
            _queue_transcript("assistant", message)
        
        @session.on("agent_speech_interrupted")
        def on_agent_interrupted():
            logger.info("⚡ User interrupted! AI stopped speaking to listen...")
        
        @session.on("user_state_changed")
        def on_user_state_changed(state):
            logger.info(f"👥 User state changed: {state}")
        
        # Start the assistant session with the agent and room
        await session.start(agent, room=ctx.room)
        logger.info("🎙️ Voice assistant started and listening for real-time voice streaming...")
        
        # Send initial greeting when user connects
        greeting_message = (
            "Hello! Welcome to Attar Travel. I'm your AI travel assistant for Saudi Arabia. "
            "How can I help you plan your perfect journey today?"
        )
        await session.say(greeting_message, allow_interruptions=True)
        logger.info(f"👋 Sent greeting to user: {greeting_message}")
        
        # Keep the session alive for continuous streaming
        # The session will handle bidirectional audio automatically
        await asyncio.Event().wait()  # Wait indefinitely until disconnected


async def request_handler(job_request: agents.JobRequest) -> None:
    """
    Handler for incoming job requests
    This decides whether the agent should accept a room session
    """
    logger.info(f"📨 Received job request for room: {job_request.room.name}")
    
    # Accept all room requests in development/production
    await job_request.accept()
    logger.info(f"✅ Job accepted for room: {job_request.room.name}")


def run_livekit_agent():
    """Function to run the LiveKit agent - can be called from main.py"""
    # Initialize the assistant
    assistant = AttarTravelVoiceAssistant()
    
    # Run the agent with LiveKit
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=assistant.entrypoint,
            request_fnc=request_handler,
        )
    )


if __name__ == "__main__":
    run_livekit_agent()



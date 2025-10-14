"""
LiveKit Voice Agent with OpenAI Realtime API
Real-time multilingual travel assistant for Saudi Arabia (Attar Travel)
"""

import asyncio
import logging
import os
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

    async def entrypoint(self, ctx: JobContext):
        """
        Called when the agent joins a LiveKit room.
        Handles connection, session setup, and AI behavior.
        """
        logger.info(f"🚀 Joining LiveKit room: {ctx.room.name}")

        # Connect to the room
        await ctx.connect()
        logger.info(f"✅ Connected to room: {ctx.room.name}")

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
        @session.on("user_speech_started")
        def _on_user_speech_started():
            logger.info("👂 User started speaking...")

        @session.on("user_speech_committed")
        def _on_user_speech_committed(msg):
            logger.info(f"👤 User said: {getattr(msg, 'content', msg)}")

        @session.on("agent_speech_started")
        def _on_agent_speech_started():
            logger.info("🗣️ Agent started speaking...")

        @session.on("agent_speech_committed")
        def _on_agent_speech_committed(msg):
            logger.info(f"🤖 Agent said: {getattr(msg, 'content', msg)}")

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
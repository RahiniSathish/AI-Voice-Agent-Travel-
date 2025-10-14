"""
LiveKit Voice Agent with OpenAI Realtime API
Real-time voice conversation agent that joins LiveKit rooms
Integrated with Attar Travel AI system
"""

import asyncio
import logging
from typing import Optional
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import openai, silero
import os
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
    
    async def entrypoint(self, ctx: JobContext):
        """
        Main entry point when agent joins a LiveKit room
        This is called automatically when a room session starts
        """
        logger.info(f"🚀 Agent joining room: {ctx.room.name}")
        
        # Connect to the room
        await ctx.connect()
        logger.info(f"✅ Agent connected to room: {ctx.room.name}")
        
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
        @session.on("user_speech_started")
        def on_user_speech_started():
            logger.info("👂 User started speaking...")
        
        @session.on("user_speech_committed")
        def on_user_speech_committed(message):
            logger.info(f"👤 User said: {message.content if hasattr(message, 'content') else message}")
        
        @session.on("agent_speech_started")
        def on_agent_speech_started():
            logger.info("🗣️ Agent started speaking...")
        
        @session.on("agent_speech_committed")
        def on_agent_speech_committed(message):
            logger.info(f"🤖 Agent said: {message.content if hasattr(message, 'content') else message}")
        
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



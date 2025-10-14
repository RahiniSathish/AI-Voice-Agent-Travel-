"""
Main Entry Point for AI Travel Agent Backend
Launches the FastAPI application
"""

import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # Import and run the FastAPI app
    from api import app
    
    print("=" * 50)
    print("✈️  AI TRAVEL AGENT - BACKEND SERVER")
    print("=" * 50)
    print("🚀 Starting server...")
    print("📡 Host: 0.0.0.0")
    print("🔌 Port: 8000")
    print("🔊 Voice: Azure Speech Services (GuyNeural)")
    print("🤖 AI: Azure OpenAI (GPT-4)")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


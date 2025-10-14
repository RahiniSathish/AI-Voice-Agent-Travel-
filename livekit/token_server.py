

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit.api.access_token import AccessToken, VideoGrants
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="LiveKit Token Server")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    roomName: str
    participantName: str


class TokenResponse(BaseModel):
    token: str
    url: str


@app.get("/")
async def root():
    return {
        "service": "LiveKit Token Server",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/get-token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """
    Generate a LiveKit access token for a participant
    """
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        if not all([livekit_url, api_key, api_secret]):
            raise HTTPException(
                status_code=500,
                detail="LiveKit credentials not configured"
            )
        
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
        
        logger.info(f"✅ Token generated for {request.participantName} in room {request.roomName}")
        
        return TokenResponse(
            token=jwt_token,
            url=livekit_url
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("🔐 LiveKit Token Server")
    print("=" * 50)
    print("🚀 Starting server on http://0.0.0.0:3000")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )


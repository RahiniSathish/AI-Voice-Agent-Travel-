#!/usr/bin/env python
"""Test LiveKit token generation"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

print(f"Loading .env from: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")

try:
    from livekit import api as livekit_api
    print('✅ LiveKit imported successfully')
    print(f'AccessToken available: {hasattr(livekit_api, "AccessToken")}')
    print(f'VideoGrants available: {hasattr(livekit_api, "VideoGrants")}')
    
    # Check credentials
    livekit_url = os.getenv('LIVEKIT_URL')
    api_key = os.getenv('LIVEKIT_API_KEY')
    api_secret = os.getenv('LIVEKIT_API_SECRET')
    
    print(f'\nCredentials check:')
    print(f'LIVEKIT_URL: {livekit_url if livekit_url else "❌ NOT SET"}')
    print(f'LIVEKIT_API_KEY: {api_key[:15] + "..." if api_key else "❌ NOT SET"}')
    print(f'LIVEKIT_API_SECRET: {api_secret[:15] + "..." if api_secret else "❌ NOT SET"}')
    
    if not all([livekit_url, api_key, api_secret]):
        print('\n❌ Missing credentials!')
        sys.exit(1)
    
    # Test token generation
    print('\n🧪 Testing token generation...')
    token = livekit_api.AccessToken(api_key, api_secret) \
        .with_identity('TestUser') \
        .with_name('TestUser') \
        .with_grants(livekit_api.VideoGrants(
            room_join=True,
            room='test-room',
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        ))
    
    jwt_token = token.to_jwt()
    print(f'✅ Token generated successfully!')
    print(f'Token (first 50 chars): {jwt_token[:50]}...')
    print(f'Token length: {len(jwt_token)}')
    
except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('\n✅ All tests passed!')


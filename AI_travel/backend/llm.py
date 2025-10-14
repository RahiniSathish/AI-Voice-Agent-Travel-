"""
LLM and Speech Services Integration
Handles Azure OpenAI and Azure Speech Services
"""

import os
import logging
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from datetime import datetime
import base64
from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    LANGUAGE_VOICES,
    TRAVEL_CONTEXT
)

logger = logging.getLogger(__name__)

# Azure OpenAI Client
azure_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Azure Speech Configuration
speech_config = speechsdk.SpeechConfig(
    subscription=AZURE_SPEECH_KEY, 
    region=AZURE_SPEECH_REGION
)

# Auto-detect language configuration for recognition (max 4 languages)
auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
    languages=["en-US", "ta-IN", "hi-IN", "te-IN"]
)

# Conversation history (in-memory storage for current sessions)
conversation_history = {}

def detect_language(text):
    """Simple language detection based on text"""
    # Tamil detection
    if any('\u0B80' <= char <= '\u0BFF' for char in text):
        return 'ta'
    # Hindi detection
    elif any('\u0900' <= char <= '\u097F' for char in text):
        return 'hi'
    # Telugu detection  
    elif any('\u0C00' <= char <= '\u0C7F' for char in text):
        return 'te'
    # Kannada detection
    elif any('\u0C80' <= char <= '\u0CFF' for char in text):
        return 'kn'
    else:
        return 'en'

def get_ai_response(session_id, user_message):
    """Get AI response from Azure OpenAI"""
    try:
        # Get or create conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = [
                {"role": "system", "content": TRAVEL_CONTEXT}
            ]
        
        # Add user message
        conversation_history[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Get AI response
        response = azure_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=conversation_history[session_id],
            max_tokens=300,
            temperature=0.8
        )
        
        ai_message = response.choices[0].message.content.strip()
        
        # Add AI response to history
        conversation_history[session_id].append({
            "role": "assistant",
            "content": ai_message
        })
        
        # Keep only last 10 messages to prevent context overflow
        if len(conversation_history[session_id]) > 21:  # 1 system + 20 messages
            conversation_history[session_id] = [conversation_history[session_id][0]] + conversation_history[session_id][-20:]
        
        return ai_message
    except Exception as e:
        logger.error(f"❌ AI Response Error: {str(e)}")
        raise

def speech_to_text(file_path):
    """Convert speech to text using Azure Speech Services with auto language detection"""
    try:
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        
        # Use auto-detect source language recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            auto_detect_source_language_config=auto_detect_source_language_config,
            audio_config=audio_config
        )
        
        logger.info("🎤 Azure Speech: Transcribing (multilingual)...")
        result = speech_recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            detected_language = result.properties.get(speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult)
            logger.info(f"✅ Transcription successful (Language: {detected_language})")
            return result.text.strip(), detected_language
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("⚠️ No speech detected")
            return None, None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"❌ Recognition canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error(f"   Error: {cancellation.error_details}")
            return None, None
        else:
            logger.warning(f"⚠️ Unexpected result: {result.reason}")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ STT Exception: {type(e).__name__} - {str(e)}")
        return None, None

def text_to_speech(text, language_code='en-US'):
    """Convert text to speech using Azure Speech Services with language support"""
    if not text:
        return None
    
    try:
        # Get language prefix (en from en-US)
        lang_prefix = language_code.split('-')[0] if language_code else 'en'
        
        # Select appropriate voice based on language
        voice_name = LANGUAGE_VOICES.get(lang_prefix, 'en-US-GuyNeural')
        
        # Create new speech config with selected voice
        tts_speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        tts_speech_config.speech_synthesis_voice_name = voice_name
        
        speech_file_path = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_speech.wav"
        audio_config = speechsdk.audio.AudioOutputConfig(filename=speech_file_path)
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=tts_speech_config,
            audio_config=audio_config
        )
        
        logger.info(f"🔊 Azure Speech: Synthesizing in {voice_name}...")
        result = speech_synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info("✅ Audio synthesis completed")
            
            with open(speech_file_path, "rb") as f:
                audio_data = f.read()
            
            os.remove(speech_file_path)
            return audio_data
            
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"❌ TTS canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error(f"   Error: {cancellation.error_details}")
            
            if os.path.exists(speech_file_path):
                os.remove(speech_file_path)
            return None
        else:
            logger.warning(f"⚠️ Unexpected TTS result: {result.reason}")
            if os.path.exists(speech_file_path):
                os.remove(speech_file_path)
            return None
            
    except Exception as e:
        logger.error(f"❌ TTS Exception: {type(e).__name__} - {str(e)}")
        if 'speech_file_path' in locals() and os.path.exists(speech_file_path):
            try:
                os.remove(speech_file_path)
            except:
                pass
        return None

def clear_conversation_history(session_id):
    """Clear conversation history for a session"""
    if session_id in conversation_history:
        del conversation_history[session_id]
        return True
    return False


import os
from elevenlabs.client import ElevenLabs

def generate_speech(text, voice_id=None):
    """
    Generate speech audio from text using ElevenLabs
    
    Args:
        text (str): Text to convert to speech
        voice_id (str, optional): Voice ID to use
        
    Returns:
        bytes: Audio data in MP3 format
    """
    api_key = os.environ.get('ELEVENLABS_API_KEY')
    if not api_key:
        raise ValueError("ElevenLabs API key not found in environment variables")
    
    client = ElevenLabs(api_key=api_key)
    
    audio = client.generate(
        text=text,
        voice=voice_id if voice_id and voice_id != "default" else None,
        model="eleven_multilingual_v2"
    )
    
    # Convert audio to bytes
    if hasattr(audio, 'content'):
        # If audio is a response object
        return audio.content
    elif hasattr(audio, 'read'):
        # If audio is a file-like object
        return audio.read()
    else:
        # If audio is already bytes
        return audio
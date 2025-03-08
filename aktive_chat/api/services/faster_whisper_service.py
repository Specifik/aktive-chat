# api/services/faster_whisper_service.py
import os
import tempfile
import uuid
import torch
from faster_whisper import WhisperModel
from threading import Thread
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Cache for active transcription sessions
active_sessions = {}

def get_device():
    """Get the appropriate device for running the model"""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        return "mps"  # For Apple Silicon
    else:
        return "cpu"

def initialize_model():
    """Initialize the Faster Whisper model"""
    device = get_device()
    compute_type = "float16" if device == "cuda" else "int8"
    
    # Use the small model by default
    model_size = os.environ.get("WHISPER_MODEL_SIZE", "small")
    
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return model

# Global model instance
whisper_model = None

def get_model():
    """Get or initialize the Whisper model"""
    global whisper_model
    if whisper_model is None:
        whisper_model = initialize_model()
    return whisper_model

def create_transcription_session(user_id):
    """Create a new transcription session"""
    session_id = str(uuid.uuid4())
    
    # Store session info
    active_sessions[session_id] = {
        'user_id': user_id,
        'status': 'initialized',
        'temp_files': []
    }
    
    return session_id

def process_audio_chunk(session_id, audio_data, language=None):
    """
    Process an audio chunk for transcription
    
    Args:
        session_id (str): Session ID
        audio_data (bytes): Raw audio data in webm format
        language (str, optional): Source language code (e.g., 'en', 'fr')
    
    Returns:
        dict: Transcription result
    """
    if session_id not in active_sessions:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    # Create a temporary file for the audio chunk
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_filename = temp_file.name
    
    # Store temp file for later cleanup
    active_sessions[session_id]['temp_files'].append(temp_filename)
    
    # Use the model to transcribe
    try:
        model = get_model()
        
        # Set language if provided
        whisper_language = language if language else None
        
        # Start transcription in a separate thread to not block
        def run_transcription():
            try:
                # Set status to processing
                active_sessions[session_id]['status'] = 'processing'
                
                # Transcribe the audio
                segments, info = model.transcribe(
                    temp_filename,
                    language=whisper_language,
                    beam_size=5,
                    vad_filter=True
                )
                
                # Process segments
                results = []
                for segment in segments:
                    results.append({
                        'text': segment.text,
                        'start': segment.start,
                        'end': segment.end,
                        'confidence': segment.avg_logprob
                    })
                
                # If we have results, send them to the WebSocket
                if results:
                    user_id = active_sessions[session_id]['user_id']
                    channel_layer = get_channel_layer()
                    
                    # Send to the user's channel group
                    async_to_sync(channel_layer.group_send)(
                        f"user_{user_id}",
                        {
                            'type': 'transcription_message',
                            'message': {
                                'session_id': session_id,
                                'language': info.language,
                                'segments': results,
                                'is_final': True
                            }
                        }
                    )
                
                # Set status to completed
                active_sessions[session_id]['status'] = 'completed'
                
            except Exception as e:
                # Set status to error
                active_sessions[session_id]['status'] = 'error'
                active_sessions[session_id]['error'] = str(e)
                
                # Send error to WebSocket
                user_id = active_sessions[session_id]['user_id']
                channel_layer = get_channel_layer()
                
                async_to_sync(channel_layer.group_send)(
                    f"user_{user_id}",
                    {
                        'type': 'transcription_message',
                        'message': {
                            'session_id': session_id,
                            'error': str(e)
                        }
                    }
                )
                
                # Clean up temporary file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
        
        # Start transcription in background
        thread = Thread(target=run_transcription)
        thread.daemon = True
        thread.start()
        
        return {
            'session_id': session_id,
            'status': 'processing'
        }
        
    except Exception as e:
        # Update session status
        active_sessions[session_id]['status'] = 'error'
        active_sessions[session_id]['error'] = str(e)
        
        # Clean up temporary file
        try:
            os.unlink(temp_filename)
        except:
            pass
        
        raise

def close_transcription_session(session_id):
    """
    Close an active transcription session and clean up resources
    
    Args:
        session_id (str): Session ID
    """
    if session_id not in active_sessions:
        return
    
    # Clean up temporary files
    for temp_file in active_sessions[session_id].get('temp_files', []):
        try:
            os.unlink(temp_file)
        except:
            pass
    
    # Remove session
    del active_sessions[session_id]
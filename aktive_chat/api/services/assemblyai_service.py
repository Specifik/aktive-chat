import os
import assemblyai as aai
import uuid
from threading import Thread

# Active transcription sessions
active_sessions = {}

def create_transcription_session(callback=None):
    """
    Create a new transcription session with AssemblyAI
    
    Args:
        callback (callable): Function to call with transcription data
        
    Returns:
        str: Session ID
    """
    api_key = os.environ.get('ASSEMBLYAI_API_KEY')
    if not api_key:
        raise ValueError("AssemblyAI API key not found in environment variables")
    
    aai.settings.api_key = api_key
    
    def on_open(session_opened):
        """Handler for when connection is established"""
        if callback:
            callback({
                'event': 'connected',
                'sessionId': session_opened.session_id
            })
    
    def on_data(transcript):
        """Handler for when transcript data is received"""
        if not transcript.text:
            return
            
        if callback:
            callback({
                'event': 'transcript',
                'text': transcript.text,
                'isFinal': isinstance(transcript, aai.RealtimeFinalTranscript)
            })
    
    def on_error(error):
        """Handler for errors"""
        if callback:
            callback({
                'event': 'error',
                'error': str(error)
            })
    
    def on_close():
        """Handler for when connection is closed"""
        if callback:
            callback({
                'event': 'disconnected'
            })
    
    # Create transcriber
    transcriber = aai.RealtimeTranscriber(
        on_data=on_data,
        on_error=on_error,
        sample_rate=44_100,
        on_open=on_open,
        on_close=on_close
    )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Store transcriber
    active_sessions[session_id] = {
        'transcriber': transcriber,
        'status': 'initialized'
    }
    
    # Connect in background thread
    def connect_transcriber():
        try:
            active_sessions[session_id]['status'] = 'connecting'
            transcriber.connect()
            active_sessions[session_id]['status'] = 'connected'
        except Exception as e:
            active_sessions[session_id]['status'] = 'error'
            active_sessions[session_id]['error'] = str(e)
    
    thread = Thread(target=connect_transcriber)
    thread.daemon = True
    thread.start()
    
    return session_id

def process_audio_chunk(session_id, audio_data):
    """
    Process audio chunk for transcription
    
    Args:
        session_id (str): Session ID
        audio_data (bytes): Raw audio data
    """
    if session_id not in active_sessions:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    session = active_sessions[session_id]
    if session['status'] != 'connected':
        raise ValueError(f"Session not connected. Status: {session['status']}")
    
    transcriber = session['transcriber']
    # Process the audio data (implementation depends on AssemblyAI)
    # This is a simplified version - in production you'd need to format the audio correctly
    transcriber.process_audio(audio_data)

def close_transcription_session(session_id):
    """
    Close an active transcription session
    
    Args:
        session_id (str): Session ID
    """
    if session_id not in active_sessions:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    session = active_sessions[session_id]
    transcriber = session['transcriber']
    
    # Close the transcriber
    transcriber.close()
    
    # Remove from active sessions
    del active_sessions[session_id]
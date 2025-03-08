import os
import sys
import django
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aktive_chat.settings')
django.setup()

# Try to import the transcription service
try:
    from api.services.faster_whisper_service import get_model
    
    def test_faster_whisper():
        """Test the Faster Whisper speech recognition"""
        print("Initializing Faster Whisper model (this may take a moment)...")
        start_time = time.time()
        
        try:
            # Get the model
            model = get_model()
            init_time = time.time() - start_time
            print(f"Model initialized in {init_time:.2f} seconds")
            
            # Test audio file path - you need to have this file
            # You can use any WAV or MP3 file for testing
            test_audio = "test_audio.mp3"
            
            if not os.path.exists(test_audio):
                print(f"Test audio file {test_audio} not found. Creating a simple test instruction.")
                print("Please provide an audio file named 'test_audio.mp3' in the current directory.")
                return
            
            print(f"Transcribing {test_audio}...")
            transcribe_start = time.time()
            
            # Perform transcription
            segments, info = model.transcribe(test_audio, beam_size=5, vad_filter=True)
            
            # Process results
            segments_list = list(segments)  # Convert generator to list
            transcribe_time = time.time() - transcribe_start
            
            print(f"Transcription completed in {transcribe_time:.2f} seconds")
            print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            print(f"Number of segments: {len(segments_list)}")
            
            print("\nTranscription results:")
            for i, segment in enumerate(segments_list[:5]):  # Show first 5 segments
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
            if len(segments_list) > 5:
                print("...")
            
            print("Faster Whisper test successful!")
            
        except Exception as e:
            print(f"Faster Whisper test failed: {str(e)}")
    
    if __name__ == "__main__":
        test_faster_whisper()
        
except ImportError as e:
    print(f"Import error: {str(e)}")
    print("Make sure faster-whisper is installed correctly with: pip install faster-whisper")
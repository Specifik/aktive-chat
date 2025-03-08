import os
import sys
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aktive_chat.settings')
django.setup()

# Import after Django setup
from api.services.google_translate_service import translate_text, get_supported_languages

def test_translation():
    """Test the translation service"""
    text = "Hello, how are you today?"
    target_language = "fr"  # French
    
    print(f"Translating: '{text}' to {target_language}")
    
    try:
        result = translate_text(text, target_language)
        print(f"Translation: {result['translated_text']}")
        print(f"Detected source language: {result['detected_source']}")
        print("Translation test successful!")
    except Exception as e:
        print(f"Translation test failed: {str(e)}")

def test_languages():
    """Test getting supported languages"""
    try:
        languages = get_supported_languages()
        print(f"Found {len(languages)} supported languages")
        print("Sample languages:")
        for lang in languages[:5]:  # Show first 5 languages
            print(f"  - {lang['name']} ({lang['code']})")
        print("Languages test successful!")
    except Exception as e:
        print(f"Languages test failed: {str(e)}")

if __name__ == "__main__":
    test_translation()
    print("\n" + "-" * 40 + "\n")
    test_languages()
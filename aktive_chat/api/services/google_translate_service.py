# api/services/google_translate_service.py
import os
import html
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import json

# Global translator client
translator = None

def get_translator():
    """Get or initialize the Google Translate client"""
    global translator
    if translator is None:
        # Check if credentials are in environment variable
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            translator = translate.Client()
        elif 'GOOGLE_CREDENTIALS_JSON' in os.environ:
            # Load credentials from JSON string in environment variable
            credentials_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
            credentials = service_account.Credentials.from_service_account_info(credentials_json)
            translator = translate.Client(credentials=credentials)
        else:
            raise ValueError("Google Cloud credentials not found in environment variables")
    
    return translator

def translate_text(text, target_language, source_language=None):
    """
    Translate text using Google Translate
    
    Args:
        text (str): Text to translate
        target_language (str): Target language code (e.g., 'en', 'fr', 'de')
        source_language (str, optional): Source language code
                                         If None, Google will auto-detect the language
    
    Returns:
        str: Translated text
    """
    if not text:
        return ""
    
    try:
        client = get_translator()
        
        # Perform translation
        result = client.translate(
            text,
            target_language=target_language,
            source_language=source_language,
            format_='text'
        )
        
        # Decode HTML entities in the translation
        translated_text = html.unescape(result['translatedText'])
        detected_source = result.get('detectedSourceLanguage')
        
        return {
            'translated_text': translated_text,
            'detected_source': detected_source if not source_language else source_language
        }
        
    except Exception as e:
        raise ValueError(f"Translation error: {str(e)}")

def get_supported_languages(display_language='en'):
    """
    Get list of supported languages for translation
    
    Args:
        display_language (str): Language code for displaying language names
    
    Returns:
        list: List of language objects with code and name
    """
    try:
        client = get_translator()
        languages = client.get_languages(target_language=display_language)
        
        # Format the languages
        formatted_languages = [
            {'code': lang['language'], 'name': lang['name']}
            for lang in languages
        ]
        
        return formatted_languages
        
    except Exception as e:
        raise ValueError(f"Error fetching supported languages: {str(e)}")

# Alternative: DeepL API Integration
class DeepLTranslator:
    """DeepL API integration as an alternative to Google Translate"""
    
    def __init__(self):
        self.api_key = os.environ.get('DEEPL_API_KEY')
        if not self.api_key:
            raise ValueError("DeepL API key not found in environment variables")
        
        # Free API vs Pro API endpoint
        self.is_free_api = os.environ.get('DEEPL_FREE_API', 'true').lower() == 'true'
        self.base_url = 'https://api-free.deepl.com/v2' if self.is_free_api else 'https://api.deepl.com/v2'
    
    def translate_text(self, text, target_language, source_language=None):
        """Translate text using DeepL API"""
        import requests
        
        if not text:
            return ""
        
        try:
            # Prepare API request
            url = f"{self.base_url}/translate"
            
            params = {
                'auth_key': self.api_key,
                'text': text,
                'target_lang': target_language
            }
            
            if source_language:
                params['source_lang'] = source_language
            
            # Make API request
            response = requests.post(url, data=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            translated_text = data['translations'][0]['text']
            detected_source = data['translations'][0].get('detected_source_language')
            
            return {
                'translated_text': translated_text,
                'detected_source': detected_source
            }
            
        except Exception as e:
            raise ValueError(f"DeepL translation error: {str(e)}")
    
    def get_supported_languages(self):
        """Get list of supported languages for translation"""
        import requests
        
        try:
            # Prepare API request
            url = f"{self.base_url}/languages"
            
            params = {
                'auth_key': self.api_key,
                'type': 'target'  # Languages available as translation targets
            }
            
            # Make API request
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            languages = response.json()
            
            # Format the languages
            formatted_languages = [
                {'code': lang['language'], 'name': lang['name']}
                for lang in languages
            ]
            
            return formatted_languages
            
        except Exception as e:
            raise ValueError(f"Error fetching supported DeepL languages: {str(e)}")
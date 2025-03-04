# in api/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
def translate_text(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        target_language = data.get('language', 'French')
        
        # Call your translation service here
        # translated_text = your_translation_function(text, target_language)
        
        # For testing purposes
        translated_text = f"Translated to {target_language}: {text}"
        
        return JsonResponse({'translation': translated_text})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@csrf_exempt
def text_to_speech(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        voice_id = data.get('voiceId', '')
        
        # Call your text-to-speech service here
        # audio_url = your_tts_function(text, voice_id)
        
        # For testing purposes
        audio_url = "/static/sample_audio.mp3"
        
        return JsonResponse({'audioUrl': audio_url})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)
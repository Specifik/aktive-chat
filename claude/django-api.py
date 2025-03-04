# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import TranslationHistory, UsageRecord
from .serializers import TranslationHistorySerializer

from api.openai_service import translate_text
from api.elevenlabs_service import generate_speech
from api.assemblyai_service import process_audio_chunk, create_transcription_session

import json
import uuid
import os

@login_required
def dashboard_view(request):
    """Main dashboard view for logged-in users"""
    user = request.user
    translation_history = TranslationHistory.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'subscription': user.subscription,
        'recent_translations': translation_history,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def translator_view(request):
    """Main translator interface"""
    user = request.user
    
    context = {
        'user': user,
        'default_language': user.settings.default_language,
        'default_voice': user.settings.default_voice,
    }
    
    return render(request, 'core/translator.html', context)

# API Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_languages(request):
    """Return list of supported languages"""
    languages = [
        "Chinese", "Korean", "Dutch", "Turkish", "Swedish", "Indonesian", 
        "Filipino", "Japanese", "Ukrainian", "Greek", "Czech", "Finnish", 
        "Romanian", "Russian", "Danish", "Bulgarian", "Malay", "Slovak", 
        "Croatian", "Arabic", "Tamil", "English", "Polish", "German", 
        "Spanish", "French", "Italian", "Hindi", "Portuguese"
    ]
    return Response(languages)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def translate(request):
    """Translate text to target language"""
    user = request.user
    
    # Check if user subscription is active
    if not user.subscription.is_active():
        return Response(
            {"error": "Your subscription is inactive. Please renew to continue using translation services."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get request data
    text = request.data.get('text', '')
    target_language = request.data.get('language', 'French')
    
    if not text:
        return Response({"error": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Translate the text
        translation = translate_text(text, target_language)
        
        # Record usage
        char_count = len(text)
        UsageRecord.objects.create(
            user=user,
            service_type="translation",
            character_count=char_count,
            cost=char_count * 0.000001  # Example pricing: $0.000001 per character
        )
        
        # Save to history if enabled
        if user.settings.save_history:
            history_entry = TranslationHistory.objects.create(
                user=user,
                original_text=text,
                translated_text=translation,
                target_language=target_language
            )
        
        return Response({"translation": translation})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def text_to_speech(request):
    """Generate speech from text"""
    user = request.user
    
    # Check if user subscription is active
    if not user.subscription.is_active():
        return Response(
            {"error": "Your subscription is inactive. Please renew to continue using text-to-speech services."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get request data
    text = request.data.get('text', '')
    voice_id = request.data.get('voiceId', '')
    
    if not text:
        return Response({"error": "No text provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Generate speech
        audio_bytes = generate_speech(text, voice_id)
        
        # Create unique filename
        filename = f"{uuid.uuid4().hex}.mp3"
        directory = 'media/generated_audio/'
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, filename)
        
        # Save to file
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
        
        # Record usage
        char_count = len(text)
        UsageRecord.objects.create(
            user=user,
            service_type="text_to_speech",
            character_count=char_count,
            cost=char_count * 0.000015  # Example pricing: $0.000015 per character
        )
        
        # Return URL to audio file
        return Response({
            "audioUrl": f"/media/generated_audio/{filename}"
        })
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_translation_history(request):
    """Get user's translation history"""
    user = request.user
    
    try:
        # Get all translations or filter by params
        translations = TranslationHistory.objects.filter(user=user).order_by('-created_at')
        
        # Optional filtering
        language = request.query_params.get('language')
        if language:
            translations = translations.filter(target_language=language)
        
        # Paginate if needed
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        
        # Serialize the data
        serializer = TranslationHistorySerializer(translations[start:end], many=True)
        
        return Response({
            "history": serializer.data,
            "total": translations.count(),
            "page": page,
            "page_size": page_size
        })
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_translation_history(request, pk):
    """Delete a specific translation history entry"""
    user = request.user
    
    try:
        # Get the specific translation and verify ownership
        translation = TranslationHistory.objects.get(pk=pk, user=user)
        translation.delete()
        
        return Response({"success": True})
    
    except TranslationHistory.DoesNotExist:
        return Response(
            {"error": "Translation not found or you don't have permission to delete it"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# WebSocket related endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_transcription(request):
    """Initialize a transcription session"""
    user = request.user
    
    # Check subscription
    if not user.subscription.is_active():
        return Response(
            {"error": "Your subscription is inactive. Please renew to use transcription services."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Create a transcription session
        # In a real implementation, this would connect to the WebSocket endpoint
        session_id = str(uuid.uuid4())
        
        return Response({
            "sessionId": session_id,
            "status": "initialized"
        })
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

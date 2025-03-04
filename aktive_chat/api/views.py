from django.http import HttpResponse
from django.conf import settings
import os
import uuid

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from .services.openai_service import translate_text
from .services.elevenlabs_service import generate_speech
from .services.assemblyai_service import create_transcription_session, process_audio_chunk, close_transcription_session

from core.models import TranslationHistory, UsageRecord
from core.serializers import TranslationHistorySerializer

class LanguagesAPI(APIView):
    """API endpoint for getting supported languages"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        languages = [
            "Chinese", "Korean", "Dutch", "Turkish", "Swedish", "Indonesian", 
            "Filipino", "Japanese", "Ukrainian", "Greek", "Czech", "Finnish", 
            "Romanian", "Russian", "Danish", "Bulgarian", "Malay", "Slovak", 
            "Croatian", "Arabic", "Tamil", "English", "Polish", "German", 
            "Spanish", "French", "Italian", "Hindi", "Portuguese"
        ]
        return Response(languages)

class TranslateAPI(APIView):
    """API endpoint for translating text"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Check if user subscription is active
        if hasattr(user, 'subscription') and not user.subscription.is_active():
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
                cost=char_count * 0.000001  # Example pricing
            )
            
            # Save to history if enabled
            if hasattr(user, 'settings') and user.settings.save_history:
                history_entry = TranslationHistory.objects.create(
                    user=user,
                    original_text=text,
                    translated_text=translation,
                    target_language=target_language
                )
            
            return Response({"translation": translation})
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TextToSpeechAPI(APIView):
    """API endpoint for text-to-speech conversion"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Check if user subscription is active
        if hasattr(user, 'subscription') and not user.subscription.is_active():
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
            directory = os.path.join(settings.MEDIA_ROOT, 'generated_audio')
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
                cost=char_count * 0.000015  # Example pricing
            )
            
            # Return URL to audio file
            return Response({
                "audioUrl": f"{settings.MEDIA_URL}generated_audio/{filename}"
            })
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TranscriptionSessionAPI(APIView):
    """API endpoint for managing transcription sessions"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Start a new transcription session"""
        user = request.user
        
        # Check if user subscription is active
        if hasattr(user, 'subscription') and not user.subscription.is_active():
            return Response(
                {"error": "Your subscription is inactive. Please renew to use transcription services."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Create a transcription session
            session_id = create_transcription_session()
            
            return Response({
                "sessionId": session_id,
                "status": "initialized"
            })
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        """Stop an active transcription session"""
        session_id = request.data.get('sessionId')
        
        if not session_id:
            return Response({"error": "No session ID provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            close_transcription_session(session_id)
            return Response({"status": "closed"})
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AudioProcessAPI(APIView):
    """API endpoint for processing audio chunks"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Process an audio chunk for transcription"""
        session_id = request.data.get('sessionId')
        audio_data = request.data.get('audio')
        
        if not session_id or not audio_data:
            return Response(
                {"error": "Session ID and audio data are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            process_audio_chunk(session_id, audio_data)
            return Response({"status": "processing"})
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TranslationHistoryAPI(APIView):
    """API endpoint for managing translation history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's translation history"""
        user = request.user
        
        try:
            # Get all translations or filter by params
            translations = TranslationHistory.objects.filter(user=user).order_by('-created_at')
            
            # Optional filtering
            language = request.query_params.get('language')
            if language:
                translations = translations.filter(target_language=language)
            
            # Paginate
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            
            # Serialize
            serializer = TranslationHistorySerializer(translations[start:end], many=True)
            
            return Response({
                "history": serializer.data,
                "total": translations.count(),
                "page": page,
                "page_size": page_size
            })
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, history_id=None):
        """Delete a history entry"""
        if not history_id:
            return Response({"error": "No history ID provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            entry = TranslationHistory.objects.get(id=history_id, user=request.user)
            entry.delete()
            return Response({"status": "deleted"})
        
        except TranslationHistory.DoesNotExist:
            return Response({"error": "History entry not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
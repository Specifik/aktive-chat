# api/consumers.py
import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import uuid
import logging

# Import services
from .services.faster_whisper_service import create_transcription_session, process_audio_chunk, close_transcription_session
from .services.google_translate_service import translate_text
from .services.elevenlabs_service import generate_speech

# Configure logging
logger = logging.getLogger(__name__)
User = get_user_model()

class TranslationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        # Get user from scope (requires AuthMiddlewareStack)
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Check if subscription is active
        if not await self.is_subscription_active():
            await self.close(code=4001)  # Custom close code for inactive subscription
            return
        
        # Add user to personal group
        self.user_group = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Initialize session data
        self.session_id = None
        self.target_language = None
        self.voice_id = None
        self.subtitle_enabled = False
        self.font_style = None

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        # Clean up transcription session if active
        if self.session_id:
            await sync_to_async(close_transcription_session)(self.session_id)
        
        # Remove user from personal group
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from WebSocket"""
        if text_data:
            try:
                data = json.loads(text_data)
                command = data.get('command')
                
                if command == 'start_transcription':
                    await self.handle_start_transcription(data)
                elif command == 'stop_transcription':
                    await self.handle_stop_transcription()
                elif command == 'update_settings':
                    await self.handle_update_settings(data)
            except json.JSONDecodeError:
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
            except Exception as e:
                logger.exception("Error processing text data")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
        
        if bytes_data:
            # Process audio data if session is active
            if self.session_id:
                try:
                    await self.handle_audio_data(bytes_data)
                except Exception as e:
                    logger.exception("Error processing audio data")
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))

    async def handle_start_transcription(self, data):
        """Start a new transcription session"""
        # Get settings from request
        self.target_language = data.get('target_language', 'en')
        self.voice_id = data.get('voice_id')
        self.subtitle_enabled = data.get('subtitle_enabled', True)
        self.font_style = data.get('font_style', 'default')
        
        try:
            # Create transcription session
            session_id = await sync_to_async(create_transcription_session)(self.user.id)
            self.session_id = session_id
            
            # Log usage
            await self.log_usage_start()
            
            # Send confirmation to client
            await self.send(json.dumps({
                'type': 'session_started',
                'session_id': session_id,
                'settings': {
                    'target_language': self.target_language,
                    'subtitle_enabled': self.subtitle_enabled,
                    'font_style': self.font_style
                }
            }))
            
        except Exception as e:
            logger.exception("Error starting transcription")
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_stop_transcription(self):
        """Stop the active transcription session"""
        if self.session_id:
            try:
                # Close the transcription session
                await sync_to_async(close_transcription_session)(self.session_id)
                
                # Log end of usage
                await self.log_usage_end()
                
                # Clear session data
                self.session_id = None
                
                await self.send(json.dumps({
                    'type': 'session_stopped'
                }))
                
            except Exception as e:
                logger.exception("Error stopping transcription")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))

    async def handle_audio_data(self, audio_data):
        """Process incoming audio data"""
        if not self.session_id:
            return
        
        try:
            # Process the audio data with faster-whisper
            result = await sync_to_async(process_audio_chunk)(
                self.session_id, 
                audio_data
            )
            
            # No need to send anything here as the transcription results
            # will be sent via the transcription_message handler
            
        except Exception as e:
            logger.exception("Error processing audio")
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def handle_update_settings(self, data):
        """Update translation settings"""
        if 'target_language' in data:
            self.target_language = data['target_language']
        
        if 'voice_id' in data:
            self.voice_id = data['voice_id']
        
        if 'subtitle_enabled' in data:
            self.subtitle_enabled = data['subtitle_enabled']
        
        if 'font_style' in data:
            self.font_style = data['font_style']
        
        await self.send(json.dumps({
            'type': 'settings_updated',
            'settings': {
                'target_language': self.target_language,
                'subtitle_enabled': self.subtitle_enabled,
                'font_style': self.font_style
            }
        }))

    async def transcription_message(self, event):
        """Handle transcription messages from channel layer"""
        message = event['message']
        
        # Check if this is an error message
        if 'error' in message:
            await self.send(json.dumps({
                'type': 'transcription_error',
                'error': message['error']
            }))
            return
        
        # Process the transcription segments
        segments = message.get('segments', [])
        source_language = message.get('language')
        
        if segments:
            # Take the last segment as the one to translate
            segment = segments[-1]
            text = segment['text']
            
            try:
                # Translate the text
                translation_result = await sync_to_async(translate_text)(
                    text,
                    self.target_language,
                    source_language
                )
                
                translated_text = translation_result['translated_text']
                
                # Generate speech if needed
                audio_url = None
                if not self.subtitle_enabled or (self.subtitle_enabled and self.voice_id):
                    audio_bytes = await sync_to_async(generate_speech)(
                        translated_text,
                        self.voice_id
                    )
                    
                    # Store audio and get URL (implementation depends on your storage setup)
                    audio_url = await self.store_audio(audio_bytes)
                
                # Log translation usage
                await self.log_translation_usage(text, translated_text)
                
                # Create response
                response = {
                    'type': 'translation',
                    'original': {
                        'text': text,
                        'language': source_language,
                        'start': segment['start'],
                        'end': segment['end']
                    },
                    'translation': {
                        'text': translated_text,
                        'language': self.target_language
                    },
                    'subtitle_enabled': self.subtitle_enabled,
                    'font_style': self.font_style
                }
                
                if audio_url:
                    response['audio_url'] = audio_url
                
                # Send to WebSocket
                await self.send(json.dumps(response))
                
                # Save to history if user settings allow
                if await self.should_save_history():
                    await self.save_to_history(text, translated_text, source_language, audio_url)
                
            except Exception as e:
                logger.exception("Error translating text")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))

    @database_sync_to_async
    def store_audio(self, audio_bytes):
        """Store audio file and return URL"""
        from django.conf import settings
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.mp3"
        path = f"translation_audio/{self.user.id}/{filename}"
        
        # Save file using Django's storage system
        default_storage.save(path, ContentFile(audio_bytes))
        
        # Return URL
        return default_storage.url(path)

    @database_sync_to_async
    def is_subscription_active(self):
        """Check if user's subscription is active"""
        if not hasattr(self.user, 'subscription'):
            return False
        return self.user.subscription.is_active()

    @database_sync_to_async
    def should_save_history(self):
        """Check if user settings allow saving history"""
        return hasattr(self.user, 'settings') and self.user.settings.save_history

    @database_sync_to_async
    def save_to_history(self, original_text, translated_text, source_language, audio_url=None):
        """Save translation to history"""
        from core.models import TranslationHistory
        
        # Create history entry
        history = TranslationHistory(
            user=self.user,
            original_text=original_text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=self.target_language
        )
        
        # Add audio file if available
        if audio_url:
            from django.core.files.base import ContentFile
            import requests
            
            # Download the file
            response = requests.get(audio_url)
            if response.status_code == 200:
                history.translated_audio_file.save(
                    f"{uuid.uuid4().hex}.mp3",
                    ContentFile(response.content)
                )
        
        history.save()

    @database_sync_to_async
    def log_usage_start(self):
        """Log the start of usage for billing purposes"""
        from core.models import UsageRecord
        
        # Create usage record
        UsageRecord.objects.create(
            user=self.user,
            service_type='speech_to_text',
            status='started',
            session_id=self.session_id
        )

    @database_sync_to_async
    def log_usage_end(self):
        """Log the end of usage for billing purposes"""
        from core.models import UsageRecord
        
        # Find and update the usage record
        records = UsageRecord.objects.filter(
            user=self.user,
            session_id=self.session_id,
            status='started'
        )
        
        for record in records:
            record.status = 'completed'
            record.save()

    @database_sync_to_async
    def log_translation_usage(self, original_text, translated_text):
        """Log translation usage for billing purposes"""
        from core.models import UsageRecord
        
        # Create usage record
        UsageRecord.objects.create(
            user=self.user,
            service_type='translation',
            character_count=len(original_text),
            cost=len(original_text) * 0.000001  # Example pricing
        )
        
        # Log text-to-speech if applicable
        if not self.subtitle_enabled or (self.subtitle_enabled and self.voice_id):
            UsageRecord.objects.create(
                user=self.user,
                service_type='text_to_speech',
                character_count=len(translated_text),
                cost=len(translated_text) * 0.000015  # Example pricing
            )

# api/consumers.py (add this class to the existing file)

class SubtitleViewerConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for subtitle viewers"""
    
    async def connect(self):
        """Handle connection from subtitle viewer"""
        # Get token from URL route
        self.token = self.scope['url_route']['kwargs']['token']
        
        # Set up group name
        self.room_group_name = f"subtitles_{self.token}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Store viewer settings
        self.language = None
        self.viewer_id = None
        
        # Check if session exists and is valid
        session = await self.get_session()
        if not session:
            await self.close(code=4004)  # Custom close code for invalid session
            return
        
        # Accept the connection
        await self.accept()
        
        # Generate a unique viewer ID
        self.viewer_id = str(uuid.uuid4())
        
        # Log viewer connection
        await self.log_viewer_connection()
        
        # Send available languages
        languages = await self.get_available_languages()
        await self.send(json.dumps({
            'type': 'session_info',
            'session_name': session.title,
            'languages': languages,
            'current_language': self.language or 'en'  # Default to English
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Log viewer disconnection
        await self.log_viewer_disconnection()

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from WebSocket"""
        if text_data:
            try:
                data = json.loads(text_data)
                command = data.get('command')
                
                if command == 'set_language':
                    await self.handle_set_language(data)
                elif command == 'update_settings':
                    await self.handle_update_settings(data)
                elif command == 'request_history':
                    await self.handle_request_history()
                
            except json.JSONDecodeError:
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }))
            except Exception as e:
                logger.exception("Error processing viewer message")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))

    async def handle_set_language(self, data):
        """Handle language change request"""
        language = data.get('language')
        if not language:
            return
        
        # Update language preference
        self.language = language
        
        # Save preference to database
        await self.save_viewer_language()
        
        # Confirm to client
        await self.send(json.dumps({
            'type': 'settings_updated',
            'language': language
        }))

    async def handle_update_settings(self, data):
        """Handle settings update request"""
        # Check if session allows font customization
        session = await self.get_session()
        if not session or not session.allow_font_customization:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Font customization not allowed'
            }))
            return
        
        # Update session viewer settings
        viewer_settings = {}
        
        if 'font_family' in data:
            viewer_settings['font_family'] = data['font_family']
        
        if 'font_size' in data:
            viewer_settings['font_size'] = data['font_size']
        
        if 'position' in data:
            viewer_settings['position'] = data['position']
        
        if 'background_opacity' in data:
            viewer_settings['background_opacity'] = data['background_opacity']
        
        # Save settings to database
        await self.save_viewer_settings(viewer_settings)
        
        # Confirm to client
        await self.send(json.dumps({
            'type': 'settings_updated',
            'settings': viewer_settings
        }))

    async def handle_request_history(self):
        """Handle request for recent translations"""
        # Get session
        session = await self.get_session()
        if not session:
            return
        
        # Get recent translations
        history = await self.get_recent_translations()
        
        # Send to client
        await self.send(json.dumps({
            'type': 'translation_history',
            'history': history
        }))

    async def translation_message(self, event):
        """Handle translation messages from owners to distribute to viewers"""
        message = event['message']
        original_language = message.get('original_language', 'en')
        target_language = message.get('target_language', 'en')
        
        # If viewer has a language preference, translate to that language
        if self.language and self.language != target_language:
            try:
                # Get original text
                original_text = message['original']['text']
                
                # Translate to viewer's preferred language
                translation_result = await sync_to_async(translate_text)(
                    original_text,
                    self.language,
                    original_language
                )
                
                # Update message with new translation
                message['translation']['text'] = translation_result['translated_text']
                message['translation']['language'] = self.language
                
                # Generate speech if needed
                if 'audio_url' in message:
                    audio_bytes = await sync_to_async(generate_speech)(
                        translation_result['translated_text']
                    )
                    
                    # Store audio and get URL
                    audio_url = await self.store_audio(audio_bytes)
                    message['audio_url'] = audio_url
                
            except Exception as e:
                logger.exception(f"Error translating to viewer language: {self.language}")
        
        # Forward the message to the viewer
        await self.send(json.dumps(message))

    @database_sync_to_async
    def get_session(self):
        """Get shared session by token"""
        from core.models import SharedSession
        
        try:
            session = SharedSession.objects.get(access_token=self.token, is_active=True)
            
            # Check if expired
            if session.is_expired():
                return None
            
            # Increment view count
            session.increment_view_count()
            
            return session
        except SharedSession.DoesNotExist:
            return None

    @database_sync_to_async
    def get_available_languages(self):
        """Get list of available languages"""
        # Use the translation service to get supported languages
        from api.services.google_translate_service import get_supported_languages
        
        try:
            return get_supported_languages()
        except Exception as e:
            logger.exception("Error getting supported languages")
            return [
                {'code': 'en', 'name': 'English'},
                {'code': 'fr', 'name': 'French'},
                {'code': 'es', 'name': 'Spanish'},
                {'code': 'de', 'name': 'German'},
                {'code': 'it', 'name': 'Italian'}
            ]

    @database_sync_to_async
    def log_viewer_connection(self):
        """Log viewer connection to database"""
        from core.models import SharedSessionViewer, SharedSession
        
        try:
            session = SharedSession.objects.get(access_token=self.token)
            
            # Get client IP and user agent
            client_ip = self.scope.get('client')[0] if 'client' in self.scope else None
            user_agent = self.scope.get('headers', {}).get('user-agent', '')
            
            # Create or update viewer record
            viewer, created = SharedSessionViewer.objects.get_or_create(
                session=session,
                viewer_id=self.viewer_id,
                defaults={
                    'ip_address': client_ip,
                    'user_agent': user_agent
                }
            )
            
            if not created:
                viewer.last_activity = timezone.now()
                viewer.save()
            
        except Exception as e:
            logger.exception("Error logging viewer connection")

    @database_sync_to_async
    def log_viewer_disconnection(self):
        """Log viewer disconnection to database"""
        from core.models import SharedSessionViewer, SharedSession
        
        try:
            if not self.viewer_id:
                return
                
            session = SharedSession.objects.get(access_token=self.token)
            
            # Update viewer record with disconnection time
            try:
                viewer = SharedSessionViewer.objects.get(
                    session=session,
                    viewer_id=self.viewer_id
                )
                
                viewer.last_activity = timezone.now()
                viewer.save()
                
            except SharedSessionViewer.DoesNotExist:
                pass
                
        except Exception as e:
            logger.exception("Error logging viewer disconnection")

    @database_sync_to_async
    def save_viewer_language(self):
        """Save viewer language preference to database"""
        from core.models import SharedSessionViewer, SharedSession
        
        try:
            if not self.viewer_id or not self.language:
                return
                
            session = SharedSession.objects.get(access_token=self.token)
            
            # Update viewer record with language preference
            try:
                viewer = SharedSessionViewer.objects.get(
                    session=session,
                    viewer_id=self.viewer_id
                )
                
                viewer.language = self.language
                viewer.save()
                
            except SharedSessionViewer.DoesNotExist:
                pass
                
        except Exception as e:
            logger.exception("Error saving viewer language")

    @database_sync_to_async
    def save_viewer_settings(self, settings):
        """Save viewer settings to database"""
        # This is a placeholder for now, as we're not currently saving individual viewer settings
        # in the database beyond language preference
        pass

    @database_sync_to_async
    def get_recent_translations(self):
        """Get recent translations for the current session"""
        from core.models import TranslationHistory, SharedSession
        
        try:
            session = SharedSession.objects.get(access_token=self.token)
            
            # Get recent translations by the session owner
            translations = TranslationHistory.objects.filter(
                user=session.owner
            ).order_by('-created_at')[:10]
            
            # Format for client
            history = []
            for item in translations:
                history.append({
                    'original': {
                        'text': item.original_text,
                        'language': item.source_language or 'en'
                    },
                    'translation': {
                        'text': item.translated_text,
                        'language': item.target_language
                    },
                    'timestamp': item.created_at.isoformat()
                })
            
            return history
                
        except Exception as e:
            logger.exception("Error getting recent translations")
            return []

    @database_sync_to_async
    def store_audio(self, audio_bytes):
        """Store audio file and return URL"""
        from django.conf import settings
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.mp3"
        path = f"translation_audio/shared/{self.token}/{filename}"
        
        # Save file using Django's storage system
        default_storage.save(path, ContentFile(audio_bytes))
        
        # Return URL
        return default_storage.url(path)
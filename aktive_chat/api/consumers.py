import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
import base64
import uuid

from .services.assemblyai_service import create_transcription_session

User = get_user_model()

class TranscriptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from scope (requires AuthMiddlewareStack)
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Check if subscription is active
        if not await self.is_subscription_active():
            await self.close()
            return
        
        # Accept the connection
        await self.accept()
        
        # Initialize session data
        self.session_id = None
        self.transcriber = None

    async def disconnect(self, close_code):
        # Clean up transcription session if active
        if self.session_id:
            await self.stop_transcription()

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from WebSocket"""
        if text_data:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'start_transcription':
                await self.start_transcription()
            elif command == 'stop_transcription':
                await self.stop_transcription()
        
        if bytes_data:
            # Process audio data
            if self.session_id:
                await self.process_audio(bytes_data)

    async def start_transcription(self):
        """Start a new transcription session"""
        try:
            # Define callback function for transcription events
            def transcription_callback(data):
                # Send data to WebSocket
                self.send_transcription_data(data)
            
            # Create transcription session
            session_id = await sync_to_async(create_transcription_session)(
                callback=transcription_callback
            )
            
            self.session_id = session_id
            
            # Send confirmation to client
            await self.send(json.dumps({
                'type': 'session_started',
                'session_id': session_id
            }))
            
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def stop_transcription(self):
        """Stop the active transcription session"""
        if self.session_id:
            # Close the transcription session
            # Implementation depends on how you've set up your service
            self.session_id = None
            
            await self.send(json.dumps({
                'type': 'session_stopped'
            }))

    async def process_audio(self, audio_data):
        """Process incoming audio data"""
        if not self.session_id:
            return
        
        try:
            # Process the audio data
            # Implementation depends on how you've set up your service
            pass
            
        except Exception as e:
            await self.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    def send_transcription_data(self, data):
        """Send transcription data to WebSocket client"""
        self.send(json.dumps({
            'type': 'transcription_data',
            'data': data
        }))

    @database_sync_to_async
    def is_subscription_active(self):
        """Check if user's subscription is active"""
        if not hasattr(self.user, 'subscription'):
            return False
        return self.user.subscription.is_active()
from django.db import models
from django.conf import settings

class UsageRecord(models.Model):
    """Record of API usage for billing and quotas"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_records')
    
    # Recording timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Service used
    SERVICE_TYPES = (
        ('speech_to_text', 'Speech to Text'),
        ('translation', 'Translation'),
        ('text_to_speech', 'Text to Speech'),
    )
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    
    # Usage metrics
    audio_duration_seconds = models.FloatField(default=0)  # Duration of processed audio
    character_count = models.IntegerField(default=0)  # Number of characters processed
    
    # Cost calculation
    cost = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    def __str__(self):
        return f"{self.user.email} - {self.service_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class SavedVoice(models.Model):
    """Voice models saved by users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_voices')
    name = models.CharField(max_length=100)
    
    # Voice provider IDs
    provider = models.CharField(max_length=50, default='elevenlabs')
    provider_voice_id = models.CharField(max_length=100)
    
    # Voice characteristics
    language = models.CharField(max_length=50)
    is_cloned = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"

class TranslationHistory(models.Model):
    """History of translations for a user"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='translation_history')
    
    # Translation details
    original_text = models.TextField()
    translated_text = models.TextField()
    source_language = models.CharField(max_length=50, null=True, blank=True)
    target_language = models.CharField(max_length=50)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    favorited = models.BooleanField(default=False)
    
    # Audio files (optional)
    original_audio_file = models.FileField(upload_to='translation_audio/', null=True, blank=True)
    translated_audio_file = models.FileField(upload_to='translation_audio/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.source_language} to {self.target_language} - {self.created_at.strftime('%Y-%m-%d')}"
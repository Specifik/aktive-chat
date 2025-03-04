# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Extended user model with additional fields for account management
    """
    # Using email as primary identifier instead of username
    email = models.EmailField(unique=True)
    
    # Profile information
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Account type and status
    ACCOUNT_TYPES = (
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    )
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='free')
    is_email_verified = models.BooleanField(default=False)
    
    # API usage tracking
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.email

class Subscription(models.Model):
    """
    Subscription details for premium features
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    
    # Subscription status
    SUBSCRIPTION_STATUS = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trial', 'Trial'),
    )
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='trial')
    
    # Billing information
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Limits and quotas
    monthly_minutes = models.IntegerField(default=60)  # Minutes of speech processing per month
    
    # Payment information (could link to a payment processor)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and (self.end_date is None or self.end_date > timezone.now())
    
    def __str__(self):
        return f"{self.user.email} - {self.status}"

class UsageRecord(models.Model):
    """
    Record of API usage for billing and quotas
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_records')
    
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
    
    # Cost calculation (could be done dynamically based on rates)
    cost = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    
    def __str__(self):
        return f"{self.user.email} - {self.service_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class SavedVoice(models.Model):
    """
    Voice models created or saved by users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_voices')
    name = models.CharField(max_length=100)
    
    # Voice provider IDs (could be ElevenLabs or other services)
    provider = models.CharField(max_length=50, default='elevenlabs')
    provider_voice_id = models.CharField(max_length=100)
    
    # Voice characteristics
    language = models.CharField(max_length=50)
    is_cloned = models.BooleanField(default=False)  # Whether it's a cloned voice
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"

class TranslationHistory(models.Model):
    """
    History of translations for a user
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='translation_history')
    
    # Translation details
    original_text = models.TextField()
    translated_text = models.TextField()
    source_language = models.CharField(max_length=50, null=True, blank=True)  # Could be auto-detected
    target_language = models.CharField(max_length=50)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    favorited = models.BooleanField(default=False)
    
    # Audio files (optional storage of audio files)
    original_audio_file = models.FileField(upload_to='translation_audio/', null=True, blank=True)
    translated_audio_file = models.FileField(upload_to='translation_audio/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.source_language} to {self.target_language} - {self.created_at.strftime('%Y-%m-%d')}"

class UserSettings(models.Model):
    """
    User preferences and settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Default preferences
    default_language = models.CharField(max_length=50, default='French')
    default_voice = models.ForeignKey(SavedVoice, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Application settings
    auto_play_translations = models.BooleanField(default=True)
    save_history = models.BooleanField(default=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Settings for {self.user.email}"

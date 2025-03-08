from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

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
    
    # Session information
    session_id = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, default='started')
    
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

class SubtitleSettings(models.Model):
    """User-specific subtitle settings"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subtitle_settings')
    
    # Font settings
    FONT_CHOICES = (
        ('default', 'Default'),
        ('arial', 'Arial'),
        ('times', 'Times New Roman'),
        ('roboto', 'Roboto'),
        ('opensans', 'Open Sans'),
        ('montserrat', 'Montserrat'),
    )
    font_family = models.CharField(max_length=50, choices=FONT_CHOICES, default='default')
    font_size = models.IntegerField(default=24)  # Size in pixels
    font_color = models.CharField(max_length=20, default='#FFFFFF')  # White
    
    # Background settings
    background_color = models.CharField(max_length=20, default='#000000')  # Black
    background_opacity = models.FloatField(default=0.7)  # 70% opacity
    
    # Display settings
    position = models.CharField(
        max_length=20, 
        choices=(
            ('bottom', 'Bottom'),
            ('top', 'Top'),
            ('middle', 'Middle'),
        ),
        default='bottom'
    )
    
    # QR code settings
    qr_code_enabled = models.BooleanField(default=True)
    qr_code_data = models.CharField(max_length=255, blank=True, null=True)
    
    # Public access token (for viewers to access subtitles)
    public_access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return f"Subtitle Settings for {self.user.email}"

class SharedSession(models.Model):
    """A shared translation session that viewers can access"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_sessions')
    session_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Access control
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=100, blank=True, null=True)
    
    # Session settings
    allow_language_selection = models.BooleanField(default=True)
    allow_font_customization = models.BooleanField(default=False)
    
    # Stats and metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def is_expired(self):
        """Check if the session has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()
    
    def get_viewer_url(self):
        """Get the URL for viewers to access this session"""
        from django.urls import reverse
        return reverse('subtitle_viewer', kwargs={'token': self.access_token})
    
    def get_qr_code_url(self):
        """Get the URL for the QR code image"""
        from django.urls import reverse
        return reverse('session_qr_code_image', kwargs={'session_id': self.id})
    
    def increment_view_count(self):
        """Increment the view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def __str__(self):
        return f"{self.title} ({self.owner.email})"

class SharedSessionViewer(models.Model):
    """Tracks viewers of a shared session"""
    session = models.ForeignKey(SharedSession, on_delete=models.CASCADE, related_name='viewers')
    viewer_id = models.CharField(max_length=50)  # Anonymous ID for tracking
    
    # Viewer preferences
    language = models.CharField(max_length=50, blank=True, null=True)
    
    # Connection information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Session data
    first_connected = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('session', 'viewer_id')
    
    def __str__(self):
        return f"Viewer {self.viewer_id} for {self.session.title}"
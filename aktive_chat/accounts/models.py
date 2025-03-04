from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Extended user model with additional fields for account management"""
    # Using email as primary identifier
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
    
    def __str__(self):
        return self.email or self.username

class Subscription(models.Model):
    """Subscription details for premium features"""
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
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and (self.end_date is None or self.end_date > timezone.now())
    
    def __str__(self):
        return f"{self.user.email} - {self.status}"

class UserSettings(models.Model):
    """User preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Default preferences
    default_language = models.CharField(max_length=50, default='French')
    default_voice_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Application settings
    auto_play_translations = models.BooleanField(default=True)
    save_history = models.BooleanField(default=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Settings for {self.user.email}"
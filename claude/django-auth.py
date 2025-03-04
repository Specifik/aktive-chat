# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationForm(UserCreationForm):
    """Custom registration form with email as primary identifier"""
    email = forms.EmailField(max_length=254, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    """Custom login form with additional fields"""
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())
    
    class Meta:
        model = User
        fields = ('username', 'password', 'remember_me')

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, CustomLoginForm
from .models import Subscription, UserSettings

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create default subscription (free tier)
            Subscription.objects.create(user=user, status='trial')
            
            # Create default user settings
            UserSettings.objects.create(user=user)
            
            # Log the user in
            login(request, user)
            
            messages.success(request, "Registration successful. Welcome!")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please check the form.")
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                if not remember_me:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                
                messages.success(request, "Login successful.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid form submission.")
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    """User profile view"""
    user = request.user
    subscription = user.subscription
    settings = user.settings
    usage_records = user.usage_records.all().order_by('-timestamp')[:10]
    
    context = {
        'user': user,
        'subscription': subscription,
        'settings': settings,
        'usage_records': usage_records
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def settings_view(request):
    """User settings view"""
    user = request.user
    settings = user.settings
    
    if request.method == 'POST':
        # Update settings based on form submission
        settings.default_language = request.POST.get('default_language', 'French')
        settings.auto_play_translations = 'auto_play' in request.POST
        settings.save_history = 'save_history' in request.POST
        settings.email_notifications = 'email_notifications' in request.POST
        settings.save()
        
        messages.success(request, "Settings updated successfully.")
        return redirect('settings')
    
    context = {
        'settings': settings,
        'available_languages': ['English', 'French', 'Spanish', 'German', 'Italian', 'Japanese', 'Chinese']
    }
    
    return render(request, 'accounts/settings.html', context)

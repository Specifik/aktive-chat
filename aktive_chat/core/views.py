from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def home_view(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users"""
    user = request.user
    
    # Get user's recent translations
    recent_translations = user.translation_history.all().order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'recent_translations': recent_translations,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def translator_view(request):
    """Main translator interface"""
    context = {
        'user': request.user,
    }
    return render(request, 'core/translator.html', context)

def translator_view(request):
    """
    Serve the React app for the translator interface
    """
    return render(request, 'core/translator_react.html')
from django.shortcuts import render

def home_view(request):
    """Home page view"""
    return render(request, 'core/home.html')

def dashboard_view(request):
    """Dashboard view - no login required for frontend work"""
    return render(request, 'core/dashboard.html')

def translator_view(request):
    """Translator interface - no login required for frontend work"""
    return render(request, 'core/translator.html')
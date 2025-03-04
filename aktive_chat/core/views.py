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
    return render(request, 'core/dashboard.html')

@login_required
def translator_view(request):
    """Translator interface"""
    return render(request, 'core/translator.html')
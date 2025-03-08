# in api/views.py

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from core.models import SharedSession
from core.utils.qr_code import generate_session_qr_code, generate_session_qr_code_file

@login_required
@csrf_exempt
def translate_text(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        target_language = data.get('language', 'French')
        
        # Call your translation service here
        # translated_text = your_translation_function(text, target_language)
        
        # For testing purposes
        translated_text = f"Translated to {target_language}: {text}"
        
        return JsonResponse({'translation': translated_text})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@csrf_exempt
def text_to_speech(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        voice_id = data.get('voiceId', '')
        
        # Call your text-to-speech service here
        # audio_url = your_tts_function(text, voice_id)
        
        # For testing purposes
        audio_url = "/static/sample_audio.mp3"
        
        return JsonResponse({'audioUrl': audio_url})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@require_GET
def session_qr_code_json(request, session_id):
    """Return a base64-encoded QR code for a shared session"""
    session = get_object_or_404(SharedSession, id=session_id, owner=request.user)
    
    # Generate QR code
    qr_base64 = generate_session_qr_code(session, request)
    
    return JsonResponse({
        'qr_code': qr_base64,
        'session_url': request.build_absolute_uri(session.get_viewer_url())
    })

@login_required
@require_GET
def session_qr_code_image(request, session_id):
    """Return a QR code image for a shared session"""
    session = get_object_or_404(SharedSession, id=session_id, owner=request.user)
    
    # Generate QR code
    qr_image = generate_session_qr_code_file(session, request)
    
    # Return as PNG image
    response = HttpResponse(qr_image.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr-code-{session_id}.png"'
    
    return response

@require_GET
def public_session_qr_code(request, token):
    """Return a QR code image for a shared session by token (public access)"""
    session = get_object_or_404(SharedSession, access_token=token, is_active=True)
    
    # Check if session is expired
    if session.is_expired():
        return HttpResponse('Session expired', status=404)
    
    # Generate QR code
    qr_image = generate_session_qr_code_file(session, request)
    
    # Return as PNG image
    response = HttpResponse(qr_image.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr-code-{token}.png"'
    
    return response

# Add this to your core/urls.py
"""
urlpatterns = [
    # ... existing paths ...
    path('sessions/<int:session_id>/qr-code.json', views.session_qr_code_json, name='session_qr_code_json'),
    path('sessions/<int:session_id>/qr-code.png', views.session_qr_code_image, name='session_qr_code_image'),
    path('sessions/public/<uuid:token>/qr-code.png', views.public_session_qr_code, name='public_session_qr_code'),
]
"""

# Views for session management
@login_required
def create_session_view(request):
    """View for creating a new shared session"""
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled Session')
        description = request.POST.get('description', '')
        allow_language_selection = 'allow_language_selection' in request.POST
        allow_font_customization = 'allow_font_customization' in request.POST
        password_protected = 'password_protected' in request.POST
        password = request.POST.get('password', '') if password_protected else None
        expires_in_hours = int(request.POST.get('expires_in_hours', 24))
        
        # Create the shared session
        session = SharedSession(
            owner=request.user,
            title=title,
            description=description,
            session_id=str(uuid.uuid4()),
            allow_language_selection=allow_language_selection,
            allow_font_customization=allow_font_customization,
            password_protected=password_protected
        )
        
        # Set expiry time if specified
        if expires_in_hours > 0:
            session.expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)
        
        # Set password if enabled
        if password_protected and password:
            from django.contrib.auth.hashers import make_password
            session.password_hash = make_password(password)
        
        session.save()
        
        # Redirect to session detail page
        return redirect('session_detail', session_id=session.id)
    
    # GET request - show form
    return render(request, 'core/create_session.html')

@login_required
def session_detail_view(request, session_id):
    """View showing details of a shared session"""
    session = get_object_or_404(SharedSession, id=session_id, owner=request.user)
    
    # Get recent activity
    viewers = session.viewers.order_by('-last_activity')[:10]
    
    context = {
        'session': session,
        'viewers': viewers,
        'qr_code_url': request.build_absolute_uri(reverse('session_qr_code_image', kwargs={'session_id': session_id})),
        'viewer_url': request.build_absolute_uri(session.get_viewer_url())
    }
    
    return render(request, 'core/session_detail.html', context)

@login_required
def sessions_list_view(request):
    """View listing all shared sessions for a user"""
    sessions = SharedSession.objects.filter(owner=request.user).order_by('-created_at')
    
    context = {
        'sessions': sessions
    }
    
    return render(request, 'core/sessions_list.html', context)

def subtitle_viewer_view(request, token):
    """View for accessing shared subtitles"""
    session = get_object_or_404(SharedSession, access_token=token, is_active=True)
    
    # Check if session is expired
    if session.is_expired():
        return render(request, 'core/session_expired.html')
    
    # Check if password protected
    if session.password_protected:
        if request.method == 'POST':
            password = request.POST.get('password', '')
            
            # Verify password
            from django.contrib.auth.hashers import check_password
            if not check_password(password, session.password_hash):
                return render(request, 'core/subtitle_password.html', {
                    'session': session,
                    'error': 'Invalid password'
                })
            
            # Password correct, set session cookie
            request.session[f'subtitle_access_{token}'] = True
            
        elif not request.session.get(f'subtitle_access_{token}'):
            # No valid session, show password form
            return render(request, 'core/subtitle_password.html', {
                'session': session
            })
    
    # Get viewer settings
    settings = {
        'position': 'bottom',
        'font_family': 'default',
        'font_size': 24,
        'font_color': '#FFFFFF',
        'background_color': '#000000',
        'background_opacity': 0.7
    }
    
    # Get supported languages
    from api.services.google_translate_service import get_supported_languages
    try:
        languages = get_supported_languages()
    except:
        languages = [
            {'code': 'en', 'name': 'English'},
            {'code': 'fr', 'name': 'French'},
            {'code': 'es', 'name': 'Spanish'},
            {'code': 'de', 'name': 'German'},
            {'code': 'it', 'name': 'Italian'}
        ]
    
    # Increment view count
    session.increment_view_count()
    
    context = {
        'session': session,
        'settings': settings,
        'languages': languages,
        'default_language': 'en'
    }
    
    return render(request, 'core/subtitle_viewer.html', context)
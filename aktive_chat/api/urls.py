from django.urls import path
from . import views

urlpatterns = [
    # Translation services
    path('translate/', views.translate_text, name='translate'),
    path('text-to-speech/', views.text_to_speech, name='text-to-speech'),
    path('languages/', views.get_languages, name='get_languages'),
    
    # Session management
    path('start-transcription/', views.start_transcription, name='start_transcription'),
    
    # Translation history
    path('history/', views.get_translation_history, name='get_translation_history'),
    path('history/<int:pk>/', views.delete_translation_history, name='delete_translation_history'),
    path('history/<int:pk>/favorite/', views.toggle_favorite_translation, name='toggle_favorite_translation'),
]
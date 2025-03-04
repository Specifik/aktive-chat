from django.urls import path
from . import views

urlpatterns = [
    path('languages/', views.LanguagesAPI.as_view(), name='languages'),
    path('translate/', views.TranslateAPI.as_view(), name='translate'),
    path('text-to-speech/', views.TextToSpeechAPI.as_view(), name='text-to-speech'),
    path('transcription/session/', views.TranscriptionSessionAPI.as_view(), name='transcription-session'),
    path('transcription/process/', views.AudioProcessAPI.as_view(), name='audio-process'),
    path('history/', views.TranslationHistoryAPI.as_view(), name='translation-history'),
    path('history/<int:history_id>/', views.TranslationHistoryAPI.as_view(), name='translation-history-detail'),
]
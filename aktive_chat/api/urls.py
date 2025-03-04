from django.urls import path
from . import views

urlpatterns = [
    path('translate/', views.translate_text, name='translate'),
    path('text-to-speech/', views.text_to_speech, name='text-to-speech'),
    # Add other API endpoints as needed
]
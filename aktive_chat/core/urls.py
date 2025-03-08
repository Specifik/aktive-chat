from django.urls import path
from . import views

urlpatterns = [
    # Main application routes
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('translator/', views.translator_view, name='translator'),
    
    # Session management
    path('sessions/', views.sessions_list_view, name='sessions_list'),
    path('sessions/create/', views.create_session_view, name='create_session'),
    path('sessions/<int:session_id>/', views.session_detail_view, name='session_detail'),
    path('sessions/<int:session_id>/activate/', views.activate_session_view, name='activate_session'),
    path('sessions/<int:session_id>/deactivate/', views.deactivate_session_view, name='deactivate_session'),
    path('sessions/<int:session_id>/delete/', views.delete_session_view, name='delete_session'),
    
    # QR code routes
    path('sessions/<int:session_id>/qr-code.json', views.session_qr_code_json, name='session_qr_code_json'),
    path('sessions/<int:session_id>/qr-code.png', views.session_qr_code_image, name='session_qr_code_image'),
    path('sessions/public/<uuid:token>/qr-code.png', views.public_session_qr_code, name='public_session_qr_code'),
    
    # Subtitle viewer route
    path('subtitles/<uuid:token>/', views.subtitle_viewer_view, name='subtitle_viewer'),
]
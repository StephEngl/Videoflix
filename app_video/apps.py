"""Django app configuration for video management."""
from django.apps import AppConfig


class AppVideoConfig(AppConfig):
    """Django app configuration for video processing and streaming.
    
    Handles video upload, HLS conversion, and streaming functionality.
    Automatically imports signal handlers when app is ready.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_video'

    def ready(self):
        """Import signal handlers when Django app is ready."""
        import app_video.signals

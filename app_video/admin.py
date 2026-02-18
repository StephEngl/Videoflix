"""Django admin configuration for video management."""
from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin interface configuration for Video model.
    
    Provides readonly access to processing fields and filtering
    capabilities for video management in Django admin.
    """
    list_display = ('title', 'category', 'processing_status', 'is_processed', 'created_at')
    list_filter = ('processing_status', 'category', 'is_processed')
    readonly_fields = ('thumbnail', 'processing_status', 'is_processed', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path')
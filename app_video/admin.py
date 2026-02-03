from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'processing_status', 'is_processed', 'created_at')
    list_filter = ('processing_status', 'category', 'is_processed')
    readonly_fields = ('processing_status', 'is_processed', 'hls_480p_path', 'hls_720p_path', 'hls_1080p_path')
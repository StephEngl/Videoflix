from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Video(models.Model):
    """
    Video model for storing video metadata and HLS streaming paths.
    Automatically processes uploaded videos for HLS streaming.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.FileField(upload_to='videos/thumbnails/', blank=True, null=True)
    category = models.CharField(max_length=100)

    original_video = models.FileField(upload_to='videos/original/')
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    hls_480p_path = models.CharField(max_length=500, blank=True, null=True)
    hls_720p_path = models.CharField(max_length=500, blank=True, null=True)
    hls_1080p_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Videos"
        ordering = ['created_at']

    def __str__(self):
        """Return video title as string representation."""
        return self.title
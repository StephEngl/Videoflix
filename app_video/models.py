"""Django models for video management and HLS streaming."""
import os
from django.conf import settings
from django.db import models


def video_directory_path(instance, filename):
    """
    Dynamic upload path: videos/{video_id}/{filename}.
    
    For new instances (no ID yet): videos/temp/{filename}
    """
    if instance.id is None:
        return f'videos/temp/{filename}'
    return f'videos/{instance.id}/{filename}'


CATEGORY_CHOICES = [
    ("", "--- Please select category ---"),
    ("action", "Action"),
    ("adventure", "Adventure"),
    ("animation", "Animation"),
    ("biography", "Biography"),
    ("comedy", "Comedy"),
    ("crime", "Crime"),
    ("documentary", "Documentary"),
    ("drama", "Drama"),
    ("family", "Family"),
    ("fantasy", "Fantasy"),
    ("historical", "Historical"),
    ("horror", "Horror"),
    ("musical", "Musical"),
    ("mystery", "Mystery"),
    ("romance", "Romance"),
    ("science_fiction", "Science Fiction"),
    ("sport", "Sport"),
    ("thriller", "Thriller"),
]

class Video(models.Model):
    """Model for video storage and HLS streaming management.
    
    Stores video metadata, processing status, and HLS streaming paths
    for multiple resolutions. Automatically triggers HLS conversion
    upon video upload through Django signals.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=False, default="")

    original_video = models.FileField(upload_to=video_directory_path)
    thumbnail = models.FileField(upload_to=video_directory_path, blank=True, null=True)

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
        return f"{self.title} ({self.id})"
    
    # === MEDIA DIRECTORY PROPERTIES ===
    @property
    def media_directory(self):
        """Root directory: <MEDIA_ROOT>/videos/{id}/ — always returns str or raises."""
        media_root = getattr(settings, "MEDIA_ROOT", None)
        if not media_root:
            raise RuntimeError("settings.MEDIA_ROOT is not configured")
        return os.path.join(str(media_root), "videos", str(self.id))
    
    @property
    def hls_directory(self):
        """HLS root: <MEDIA_ROOT>/videos/{id}/hls/"""
        return os.path.join(self.media_directory, "hls")
    
    @property
    def thumbnail_path(self):
        """Thumbnail full path: <MEDIA_ROOT>/videos/{id}/thumbnail.jpg"""
        return os.path.join(self.media_directory, 'thumbnail.jpg')
    
    # === HLS HELPER METHODS ===
    def get_hls_path(self, resolution):
        """Relative path for given resolution (e.g. 'videos/123/hls/720p/index.m3u8')."""
        attr = f'hls_{resolution}_path'
        return getattr(self, attr, None)
    
    def hls_full_path(self, resolution):
        """Full filesystem path for playlist."""
        rel_path = self.get_hls_path(resolution)
        return os.path.join(settings.MEDIA_ROOT, rel_path) if rel_path else None
    
    def hls_segment_dir(self, resolution):
        """Directory for segments: media/videos/{id}/hls/{resolution}/"""
        full_path = self.hls_full_path(resolution)
        return os.path.dirname(full_path) if full_path else None
    
    def create_media_structure(self):
        """Create all directories for this video."""
        os.makedirs(self.media_directory, exist_ok=True)
        os.makedirs(self.hls_directory, exist_ok=True)
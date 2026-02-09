from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Video

import django_rq

VIDEO_RESOLUTIONS = [
    ("480p", "854:480", "800k", "96k"),
    ("720p", "1280:720", "2800k", "128k"), 
    ("1080p", "1920:1080", "5000k", "192k"),
]

@receiver(post_save, sender=Video)
def video_post_save_handler(sender, instance, created, **kwargs):
    """
    Signal handler for video processing.
    Starts processing job when new video is uploaded.
    """
    if created and instance.original_video:
        def enqueue_video_processing():
            queue = django_rq.get_queue('default', autocommit=True)

            for format_data in VIDEO_RESOLUTIONS:
                from .tasks import convert_video_to_hls
                queue.enqueue(convert_video_to_hls, instance.id, *format_data)
            
            if not instance.thumbnail:
                from .tasks import create_thumbnail
                queue.enqueue(create_thumbnail, instance.id)
            
            from .tasks import create_master_playlist
            queue.enqueue(create_master_playlist, instance.id)

        transaction.on_commit(enqueue_video_processing)
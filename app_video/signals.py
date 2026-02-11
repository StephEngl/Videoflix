import os
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video
from .tasks import convert_video_to_hls, create_thumbnail, create_master_playlist, cleanup_deleted_video_files

import django_rq

VIDEO_RESOLUTIONS = [
    ("480p", "854:480", "800k", "96k"),
    ("720p", "1280:720", "2800k", "128k"), 
    ("1080p", "1920:1080", "5000k", "192k"),
]


@receiver(post_save, sender=Video)
def video_post_save_handler(sender, instance, created, **kwargs):
    """Handle video upload and start processing pipeline.
    
    Automatically starts video processing tasks when a new video is uploaded.
    Processing includes HLS conversion in multiple resolutions, thumbnail
    creation, and master playlist generation.
        
    Returns:
        None: Function schedules background tasks and returns.
    """
    if created and instance.original_video:
        def enqueue_video_processing():
            default_queue = django_rq.get_queue('default', autocommit=True)

            previous_job = None
            for format_data in VIDEO_RESOLUTIONS:
                job = default_queue.enqueue(
                    convert_video_to_hls, 
                    instance.id, 
                    *format_data,
                    depends_on=previous_job
                )
                previous_job = job
            
            if not instance.thumbnail:
                default_queue.enqueue(create_thumbnail, instance.id)
            
            default_queue.enqueue(create_master_playlist, instance.id, depends_on=previous_job)

        transaction.on_commit(enqueue_video_processing)


@receiver(post_delete, sender=Video)
def video_post_delete_handler(sender, instance, **kwargs):
    """Handle video deletion and cleanup associated files.
    
    Automatically cleans up all video-related files and directories
    when a video instance is deleted from the database. This includes
    original video files, thumbnails, and HLS conversion outputs.
        
    Returns:
        None: Function schedules background cleanup task and returns.
    """
    def enqueue_video_cleanup():
        file_paths = []
        
        if instance.original_video:
            original_path = os.path.join(settings.MEDIA_ROOT, instance.original_video.name)
            file_paths.append(original_path)
        
        if instance.thumbnail:
            thumbnail_path = os.path.join(settings.MEDIA_ROOT, instance.thumbnail.name)
            file_paths.append(thumbnail_path)
        
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(instance.id))
        file_paths.append(hls_dir)
        
        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'thumbnails', str(instance.id))
        file_paths.append(thumbnail_dir)
        
        if file_paths:
            default_queue = django_rq.get_queue('default', autocommit=True)
            default_queue.enqueue(cleanup_deleted_video_files, instance.id, file_paths)
    
    transaction.on_commit(enqueue_video_cleanup)
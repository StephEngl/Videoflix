import os
import shutil
import subprocess
from django.db import transaction
from django.conf import settings
from django_rq import job
from app_video.models import Video


@job
@transaction.atomic
def convert_video_to_hls(video_id, resolution, scale, video_bitrate, audio_bitrate):
    """
    Convert video to specific HLS resolution using FFmpeg.
    
    Args:
        video_id (int): ID of the video to convert.
        resolution (str): Target resolution (e.g., '720p', '1080p').
        scale (str): FFmpeg scale parameter (e.g., '1280:720').
        video_bitrate (str): Video bitrate (e.g., '2800k').
        audio_bitrate (str): Audio bitrate (e.g., '128k').
        
    Raises:
        Exception: If video conversion fails.
    """
    try:
        video = Video.objects.select_for_update().get(id=video_id)
        if video.processing_status == 'pending':
            video.processing_status = 'processing'
            video.save()
        
        input_path = video.original_video.path
        resolution_dir = os.path.join(video.hls_directory, resolution)
        os.makedirs(resolution_dir, exist_ok=True)
                 
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"scale={scale}",
            '-c:v', 'libx264',
            '-b:v', video_bitrate,
            '-c:a', 'aac',
            '-b:a', audio_bitrate,
            '-hls_time', '10',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', f'{resolution_dir}/segment_%03d.ts',
            f'{resolution_dir}/index.m3u8'
        ]
            
        subprocess.run(cmd, check=True)
        
        rel_path = f'videos/{video.id}/hls/{resolution}/index.m3u8'
        setattr(video, f'hls_{resolution}_path', rel_path)
        video.save()
        
    except Exception as error:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'failed'
        video.save()
        raise error


@job
@transaction.atomic
def create_thumbnail(video_id):
    """
    Create thumbnail image for video using FFmpeg.
    
    Args:
        video_id (int): ID of the video to create thumbnail for.
    """
    try:
        video = Video.objects.select_for_update().get(id=video_id)
        
        if video.thumbnail:
            return
        
        input_path = video.original_video.path
        thumbnail_path = video.thumbnail_path
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:10',
            '-vframes', '1',
            '-q:v', '2',
            thumbnail_path
        ]
        subprocess.run(cmd, check=True)
        
        video.thumbnail.name = f'videos/{video.id}/thumbnail.jpg'
        video.save(update_fields=['thumbnail'])
                
    except Exception as error:
        raise error


@job
@transaction.atomic
def create_master_playlist(video_id):
    """
    Create HLS master playlist with all available resolutions.
    
    Args:
        video_id (int): ID of the video to create master playlist for.
    """
    try:
        video = Video.objects.select_for_update().get(id=video_id)
        
        master_playlist_path = os.path.join(video.hls_directory, 'master.m3u8')
        os.makedirs(os.path.dirname(master_playlist_path), exist_ok=True)

        playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"
        
        resolutions_info = [
            ("480p", "854x480", "800000"),
            ("720p", "1280x720", "2800000"),
            ("1080p", "1920x1080", "5000000"),
        ]
        
        for resolution, resolution_str, bandwidth in resolutions_info:
            hls_path = video.get_hls_path(resolution)
            if hls_path:
                playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution_str}\n"
                playlist_content += f"{resolution}/index.m3u8\n\n"
        
        with open(master_playlist_path, 'w') as f:
            f.write(playlist_content)
        
        video.processing_status = 'completed'
        video.is_processed = True
        video.save()
                
    except Exception as error:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'failed'
        video.save()
        raise error



@job
def cleanup_deleted_video_files(video_id):
    """
    Delete complete video directory for post_delete signals.
    
    Safe: tries model first, then direct path.
    """
    paths_to_try = []
    
    try:
        video = Video.objects.get(id=video_id)
        try:
            paths_to_try.append(video.media_directory)
        except Exception:
            pass
    except Video.DoesNotExist:
        pass
    
    direct_path = os.path.join(str(getattr(settings, "MEDIA_ROOT", "")), "videos", str(video_id))
    paths_to_try.append(direct_path)
    
    for path in paths_to_try:
        if path and os.path.exists(path):
            shutil.rmtree(path)


# === Helper: Move original video from temp to final folder ===
@job
@transaction.atomic
def move_original_video_to_final_folder(video_id):
    """
    Move the original video file from the temp folder to the final videos/{id}/ folder using video.media_directory.
    Updates the FileField path and deletes the temp file.
    Args:
        video (Video): Video instance (must have an id!)
    """
    video = Video.objects.select_for_update().get(id=video_id)
    if not video.id:
        raise ValueError("Video instance must have an id before moving the file.")
    
    temp_path = video.original_video.path
    filename = os.path.basename(temp_path)

    final_dir = video.media_directory
    os.makedirs(final_dir, exist_ok=True)

    final_path = os.path.join(final_dir, filename)
    shutil.move(temp_path, final_path)

    video.original_video.name = f"videos/{video.id}/{filename}"
    video.save(update_fields=["original_video"])

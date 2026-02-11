import os
import shutil
import subprocess
from django.db import transaction
from django.conf import settings
from django.core.files import File
from django_rq import job
from app_video.models import Video


@job
@transaction.atomic
def convert_video_to_hls(video_id, resolution, scale, video_bitrate, audio_bitrate):
    """Convert video to specific HLS resolution using FFmpeg.
    
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
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video.id))
        resolution_dir = os.path.join(output_dir, resolution)
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
        
        setattr(video, f'hls_{resolution}_path', f'videos/hls/{video.id}/{resolution}/index.m3u8')
        video.save()
        
        print(f"HLS conversion completed for {resolution}: Video {video_id}")   
        
    except Exception as error:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'failed'
        video.save()
        print(f"HLS conversion failed for {resolution}: Video {video_id}")
        raise error


@job
@transaction.atomic
def create_thumbnail(video_id):
    """Create thumbnail image for video using FFmpeg.
    
    Args:
        video_id (int): ID of the video to create thumbnail for.
        
    Raises:
        Exception: If thumbnail creation fails.
        
    Returns:
        None: Function completes successfully or raises exception.
    """
    try:
        video = Video.objects.select_for_update().get(id=video_id)
        
        if video.thumbnail:
            print(f"Thumbnail already exists for video {video_id}")
            return
        
        input_path = video.original_video.path
        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'thumbnails', str(video.id))
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumbnail_path = os.path.join(thumbnail_dir, 'thumbnail.jpg')
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-q:v', '2',
            thumbnail_path
        ]
        
        subprocess.run(cmd, check=True)
        
        with open(thumbnail_path, 'rb') as f:
            video.thumbnail.save(f'{video.id}/thumbnail.jpg', File(f), save=True)
        
        print(f"Thumbnail created for video {video_id}")
        
    except Exception as error:
        print(f"Thumbnail creation failed for video {video_id}: {error}")
        raise error


@job
@transaction.atomic
def create_master_playlist(video_id):
    """Create HLS master playlist with all available resolutions.
    
    Args:
        video_id (int): ID of the video to create master playlist for.
        
    Raises:
        Exception: If master playlist creation fails.
        
    Returns:
        None: Function completes successfully or raises exception.
    """
    try:
        video = Video.objects.select_for_update().get(id=video_id)
        
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video.id))
        master_playlist_path = os.path.join(output_dir, 'master.m3u8')
        
        playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"
        
        resolutions_info = [
            ("480p", "854x480", "800000"),
            ("720p", "1280x720", "2800000"),
            ("1080p", "1920x1080", "5000000"),
        ]
        
        for resolution, resolution_str, bandwidth in resolutions_info:
            hls_path = getattr(video, f'hls_{resolution}_path', None)
            if hls_path:
                playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution_str}\n"
                playlist_content += f"{resolution}/index.m3u8\n\n"
        
        with open(master_playlist_path, 'w') as f:
            f.write(playlist_content)
        
        video.processing_status = 'completed'
        video.is_processed = True
        video.save()
        
        print(f"Master playlist created for video {video_id}")
        
    except Exception as error:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'failed'
        video.save()
        print(f"Master playlist creation failed for video {video_id}: {error}")
        raise error



@job
def cleanup_deleted_video_files(video_id, file_paths):
    """Clean up all video-related files and directories.
    
    Args:
        video_id (int): ID of the deleted video.
        file_paths (list): List of file and directory paths to remove.
        
    Raises:
        Exception: If file cleanup fails.
        
    Returns:
        None: Function completes successfully or raises exception.
    """
    try:
        for file_path in file_paths:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
                else:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
        
        print(f"File cleanup completed for video {video_id}")
        
    except Exception as error:
        print(f"File cleanup failed for video {video_id}: {error}")
        raise error
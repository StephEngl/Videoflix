import os
import shutil
import subprocess
from django.conf import settings
from django.core.files import File
from django_rq import job
from app_video.models import Video

@job('video_processing')
def convert_video_to_hls(video_id, resolution, scale, video_bitrate, audio_bitrate):
    """Background task for converting video to specific HLS resolution with FFmpeg."""
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'processing'
        video.save()
        
        # Pfade definieren
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
            
        # Verarbeitung ausführen
        subprocess.run(cmd, check=True)
        
        # Pfad im Model speichern
        setattr(video, f'hls_{resolution}_path', f'videos/hls/{video.id}/{resolution}/index.m3u8')
        video.save()
        
        print(f"HLS conversion completed for {resolution}: Video {video_id}")   
        
    except Exception as error:
        video.processing_status = 'failed'
        video.save()
        print(f"HLS conversion completed for {resolution}: Video {video_id}")
        raise error


@job('thumbnails')
def create_thumbnail(video_id):
    """Create thumbnail for video."""
    try:
        video = Video.objects.get(id=video_id)
        
        # Skip if thumbnail already exists
        if video.thumbnail:
            print(f"Thumbnail already exists for video {video_id}")
            return
        
        input_path = video.original_video.path
        thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'thumbnails', str(video.id))
        os.makedirs(thumbnail_dir, exist_ok=True)
        thumbnail_path = os.path.join(thumbnail_dir, 'thumbnail.jpg')
        
        # FFmpeg command for thumbnail
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-q:v', '2',
            thumbnail_path
        ]
        
        subprocess.run(cmd, check=True)
        
        # Save thumbnail to Model
        with open(thumbnail_path, 'rb') as f:
            video.thumbnail.save(f'{video.id}/thumbnail.jpg', File(f), save=True)
        
        print(f"Thumbnail created for video {video_id}")
        
    except Exception as error:
        print(f"Thumbnail creation failed for video {video_id}: {error}")
        raise error


@job('playlists')
def create_master_playlist(video_id):
    """Create HLS master playlist."""
    try:
        video = Video.objects.get(id=video_id)
        
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video.id))
        master_playlist_path = os.path.join(output_dir, 'master.m3u8')
        
        # Master Playlist Content
        playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"
        
        # Alle verfügbaren Auflösungen hinzufügen
        resolutions_info = [
            ("480p", "854x480", "800000"),
            ("720p", "1280x720", "2800000"),
            ("1080p", "1920x1080", "5000000"),
        ]
        
        for resolution, resolution_str, bandwidth in resolutions_info:
            hls_path = getattr(video, f'hls_{resolution}_path', None)
            if hls_path:  # Nur wenn die Auflösung existiert
                playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={resolution_str}\n"
                playlist_content += f"{resolution}/index.m3u8\n\n"
        
        # Master Playlist speichern
        with open(master_playlist_path, 'w') as f:
            f.write(playlist_content)
        
        # Video als vollständig verarbeitet markieren
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


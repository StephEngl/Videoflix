import os
import subprocess
from django.conf import settings
from django_rq import job
from app_video.models import Video

@job('default')
def process_video_task(video_id):
    """Background task für Video-Verarbeitung mit FFmpeg."""
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = 'processing'
        video.save()
        
        # Pfade definieren
        input_path = video.original_video.path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(video.id))
        os.makedirs(output_dir, exist_ok=True)
        
        # Verschiedene Auflösungen verarbeiten
        resolutions = {
            '480p': {'width': 854, 'height': 480, 'bitrate': '800k'},
            '720p': {'width': 1280, 'height': 720, 'bitrate': '2500k'},
            '1080p': {'width': 1920, 'height': 1080, 'bitrate': '5000k'},
        }
        
        for resolution, config in resolutions.items():
            resolution_dir = os.path.join(output_dir, resolution)
            os.makedirs(resolution_dir, exist_ok=True)
            
            # FFmpeg-Befehl
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vf', f"scale={config['width']}:{config['height']}",
                '-c:v', 'libx264',
                '-b:v', config['bitrate'],
                '-c:a', 'aac',
                '-b:a', '128k',
                '-hls_time', '10',
                '-hls_playlist_type', 'vod',
                '-hls_segment_filename', f'{resolution_dir}/segment_%03d.ts',
                f'{resolution_dir}/index.m3u8'
            ]
            
            # Verarbeitung ausführen
            subprocess.run(cmd, check=True)
            
            # Pfad im Model speichern
            setattr(video, f'hls_{resolution}_path', f'videos/hls/{video.id}/{resolution}/index.m3u8')
        
        # Thumbnail generieren
        thumbnail_path = os.path.join(output_dir, 'thumbnail.jpg')
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-q:v', '2',
            thumbnail_path
        ], check=True)
        
        video.thumbnail_url = f'/media/videos/hls/{video.id}/thumbnail.jpg'
        video.processing_status = 'completed'
        video.is_processed = True
        video.save()
        
    except Exception as e:
        video.processing_status = 'failed'
        video.save()
        print(f"Video processing failed: {e}")
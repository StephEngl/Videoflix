from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
from django.conf import settings
from ..models import Video
from .serializers import VideoSerializer
import os

User = get_user_model()


class VideoListView(APIView):
    """GET /api/video/"""
    def get(self, request):
        videos = Video.objects.filter(is_processed=True)
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)
    

class HLSPlaylistView(APIView):
    """GET /api/video/<int:movie_id>/<str:resolution>/index.m3u8"""
    def get(self, request, movie_id, resolution):
        try:
            video = Video.objects.get(id=movie_id, is_processed=True)
            
            # Pfad zur M3U8-Datei
            playlist_path = getattr(video, f'hls_{resolution}_path', None)
            if not playlist_path:
                return Response(
                    {"error": f"Resolution {resolution} not available"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            full_path = os.path.join(settings.MEDIA_ROOT, playlist_path)
            
            if not os.path.exists(full_path):
                return Response(
                    {"error": "Playlist not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return FileResponse(
                open(full_path, 'rb'),
                content_type='application/vnd.apple.mpegurl'
            )
            
        except Video.DoesNotExist:
            return Response(
                {"error": "Video not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class HLSSegmentView(APIView):
    """GET /api/video/<int:movie_id>/<str:resolution>/<str:segment>"""
    def get(self, request, movie_id, resolution, segment):
        try:
            video = Video.objects.get(id=movie_id, is_processed=True)

            # Prüfen ob Resolution verfügbar ist
            resolution_path = getattr(video, f'hls_{resolution}_path', None)
            if not resolution_path:
                return Response(
                    {"error": f"Resolution {resolution} not available"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Segment-Pfad basierend auf dem Video-Objekt
            segment_dir = os.path.dirname(os.path.join(settings.MEDIA_ROOT, resolution_path))
            segment_path = os.path.join(segment_dir, segment)
            
            if not os.path.exists(segment_path):
                return Response(
                    {"error": f"Segment {segment} not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return FileResponse(
                open(segment_path, 'rb'),
                content_type='video/mp2t'
            )
            
        except Video.DoesNotExist:
            return Response(
                {"error": "Video not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
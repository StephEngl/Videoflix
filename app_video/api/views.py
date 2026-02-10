import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models import Video
from .serializers import VideoSerializer

User = get_user_model()

@extend_schema(
    tags=['Video'],
    description="Retrieve list of processed videos with metadata.",
    responses={
        200: VideoSerializer(many=True),
        401: OpenApiResponse(description="Unauthorized - Authentication credentials were not provided or are invalid."),
        }
)
class VideoListView(APIView):
    """API view for retrieving processed videos."""
    
    def get(self, request):
        """Get list of all processed videos ordered by creation date.
            
        Returns:
            Response: List of video objects with metadata.
        """
        videos = Video.objects.filter(is_processed=True).order_by('-created_at')
        serializer = VideoSerializer(videos, many=True)
        return Response(serializer.data)
    

@extend_schema(
        tags=['Video'],
        description="Retrieve HLS playlist for a specific video and resolution.",
        responses={
            200: OpenApiResponse(description="HLS playlist file returned successfully."),
            401: OpenApiResponse(description="Unauthorized - Authentication credentials were not provided or are invalid."),
            404: OpenApiResponse(description="Not Found - Video or playlist not found."),
        }
    )
class HLSPlaylistView(APIView):
    """API view for serving HLS playlist files."""
    
    def get(self, request, movie_id, resolution):
        """Serve HLS playlist file for specific video and resolution.
            
        Returns:
            FileResponse: M3U8 playlist file or error response.
        """
        try:
            video = Video.objects.get(id=movie_id, is_processed=True)
            
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


@extend_schema(
    tags=['Video'],
    description="Retrieve HLS segment for a specific video, resolution, and segment name.",
    responses={
        200: OpenApiResponse(description="HLS segment file returned successfully."),
        401: OpenApiResponse(description="Unauthorized - Authentication credentials were not provided or are invalid."),
        404: OpenApiResponse(description="Not Found - Video, resolution, or segment not found."),
        }
)
class HLSSegmentView(APIView):
    """API view for serving HLS video segments."""
    
    def get(self, request, movie_id, resolution, segment):
        """Serve HLS video segment file.
        
        Args:
            resolution: Video resolution (e.g., '720p', '1080p').
            segment: Segment filename (e.g., 'segment001.ts').
            
        Returns:
            FileResponse: TS segment file or error response.
        """
        try:
            video = Video.objects.get(id=movie_id, is_processed=True)

            resolution_path = getattr(video, f'hls_{resolution}_path', None)
            if not resolution_path:
                return Response(
                    {"error": f"Resolution {resolution} not available"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
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
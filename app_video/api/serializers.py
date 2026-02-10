import os
from ..models import Video
from rest_framework import serializers


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for video objects with computed thumbnail URL.
    
    Provides read-only access to video metadata including dynamically
    generated thumbnail URLs.
    """
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_thumbnail_url(self, obj):
        """Generate absolute thumbnail URL for video.
        
        Args:
            obj: Video instance.
            
        Returns:
            str or None: Absolute thumbnail URL if thumbnail exists, None otherwise.
        """
        if obj.thumbnail:
            base_url = os.environ.get('DJANGO_BASE_URL', 'http://localhost:8000')
            return f"{base_url}{obj.thumbnail.url}"
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
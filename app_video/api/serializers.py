import os
from ..models import Video
from rest_framework import serializers


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            base_url = os.environ.get('DJANGO_BASE_URL', 'http://localhost:8000')
            return f"{base_url}{obj.thumbnail.url}"
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
from ..models import Video
from rest_framework import serializers


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.thumbnail.url)
                return obj.thumbnail.url
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
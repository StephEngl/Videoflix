"""URL configuration for video API endpoints.

This module defines URL patterns for video management and HLS video streaming,
including video listing, playlist serving, and segment delivery.
"""

from django.urls import path
from .views import VideoListView, HLSPlaylistView, HLSSegmentView


urlpatterns = [
    # Video management
    path('video/', VideoListView.as_view(), name='video-list'),
    
    # HLS streaming endpoints
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', HLSPlaylistView.as_view(), name='hls-playlist'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', HLSSegmentView.as_view(), name='hls-segment'),
]
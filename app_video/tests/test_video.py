import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestVideoAPI:
    """Test cases for video list endpoint."""

    def test_video_list_requires_auth(self, api_client):
        """Video list should require authentication."""
        response = api_client.get('/api/video/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    

    def test_video_list_with_auth(self, authenticated_api_client):
        """Authenticated user should access video list."""
        response = authenticated_api_client.get('/api/video/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)


    def test_video_list_returns_processed_videos_only(self, authenticated_api_client, processed_video, unprocessed_video):
        """Only processed videos should appear in the list."""
        response = authenticated_api_client.get('/api/video/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == processed_video.id


    def test_video_list_empty_when_no_videos(self, authenticated_api_client):
        """Empty list when no processed videos exist."""
        response = authenticated_api_client.get('/api/video/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


    def test_video_list_ordered_by_creation_date(self, authenticated_api_client):
        """Videos should be ordered by creation date (newest first)."""
        # Would need factory to create multiple videos with different dates
        pass


@pytest.mark.django_db  
class TestHLSPlaylistAPI:
    """Test cases for HLS playlist endpoint."""

    def test_hls_playlist_requires_auth(self, api_client, processed_video):
        """HLS playlist should require authentication."""
        url = f'/api/video/{processed_video.id}/720p/index.m3u8'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_hls_playlist_video_not_found(self, authenticated_api_client):
        """Should return 404 for non-existent video."""
        url = '/api/video/99999/720p/index.m3u8'
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Video not found' in response.data['error']
    
    def test_hls_playlist_unprocessed_video(self, authenticated_api_client, unprocessed_video):
        """Should return 404 for unprocessed video."""
        url = f'/api/video/{unprocessed_video.id}/720p/index.m3u8'
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_hls_playlist_invalid_resolution(self, authenticated_api_client, processed_video):
        """Should return 404 for unavailable resolution."""
        url = f'/api/video/{processed_video.id}/480p/index.m3u8'  # Only 720p exists
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Resolution 480p not available' in response.data['error']
    
    def test_hls_playlist_file_not_exists(self, authenticated_api_client, processed_video):
        """Should return 404 when playlist file doesn't exist."""
        url = f'/api/video/{processed_video.id}/720p/index.m3u8'
        response = authenticated_api_client.get(url)
        # File doesn't actually exist in test environment
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Playlist not found' in response.data['error']


@pytest.mark.django_db
class TestHLSSegmentAPI:
    """Test cases for HLS segment endpoint."""
    
    def test_hls_segment_requires_auth(self, api_client, processed_video):
        """HLS segment should require authentication."""
        url = f'/api/video/{processed_video.id}/720p/segment001.ts'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_hls_segment_video_not_found(self, authenticated_api_client):
        """Should return 404 for non-existent video."""
        url = '/api/video/99999/720p/segment001.ts'
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_hls_segment_invalid_resolution(self, authenticated_api_client, processed_video):
        """Should return 404 for unavailable resolution."""
        url = f'/api/video/{processed_video.id}/480p/segment001.ts'
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_hls_segment_file_not_exists(self, authenticated_api_client, processed_video):
        """Should return 404 when segment file doesn't exist."""
        url = f'/api/video/{processed_video.id}/720p/segment001.ts'
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Segment segment001.ts not found' in response.data['error']
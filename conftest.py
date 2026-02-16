import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from app_video.models import Video

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    """Active user for API tests."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def inactive_user():
    """Inactive user for registration/activation tests."""
    return User.objects.create_user(
        username='inactiveuser', 
        email='inactive@example.com',
        password='testpass123',
        is_active=False
    )


@pytest.fixture
def login_user():
    """User specifically for login tests with known credentials."""
    return User.objects.create_user(
        username='loginuser',
        email='login@example.com',
        password='LoginPass123!',
        is_active=True
    )


@pytest.fixture
def logged_in_api_client(api_client, login_user):
    """API Client with user logged in via cookies."""
    api_client.post(
        reverse('login'),
        {
            "email": login_user.email,
            "password": "LoginPass123!"
        }, 
        format='json'
    )
    return api_client


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API Client with authenticated active user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def processed_video():
    """Standard processed video with 720p for most tests."""
    return Video.objects.create(
        title="Test Video",
        description="A test video",
        is_processed=True,
        hls_720p_path="videos/hls/1/720p/index.m3u8"
    )


@pytest.fixture  
def unprocessed_video():
    return Video.objects.create(
        title="Unprocessed Video",
        description="An unprocessed video",
        is_processed=False
    )


@pytest.fixture
def full_processed_video():
    """Video with all resolutions for specific HLS tests."""
    return Video.objects.create(
        title="Full Test Video",
        description="A fully processed video",
        is_processed=True,
        hls_480p_path="videos/hls/2/480p/index.m3u8",
        hls_720p_path="videos/hls/2/720p/index.m3u8",
        hls_1080p_path="videos/hls/2/1080p/index.m3u8"
    )
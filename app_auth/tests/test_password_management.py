import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from test_helpers import make_activation_url


User = get_user_model()


@pytest.mark.django_db
class TestPasswordManagement:
    """Test password reset and change endpoints."""

    def test_password_reset_request(self, api_client, user):
        """Test requesting a password reset email."""
        url = reverse('password_reset')
        data = {"email": user.email}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        assert "an email has been sent to reset your password." in response.data['detail'].lower()
        
        # Check that an email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]
        assert "reset your videoflix password" in mail.outbox[0].subject.lower()


    def test_password_reset_invalid_token(self, api_client, user):
        """Test password reset with invalid token."""
        url = make_activation_url(user, valid_token=False, url_name='password_confirm')
        
        data = {
            "new_password": "NewSecurePass123!",
            "confirm_password": "NewSecurePass123!"
        }
        
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_nonexistent_email(self, api_client):
        """Test password reset request with non-existent email."""
        url = reverse('password_reset')
        data = {"email": "nonexistent@example.com"}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        
        assert len(mail.outbox) == 0

    def test_password_reset_missing_email(self, api_client):
        """Test password reset request without email field."""
        url = reverse('password_reset')
        data = {}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'required' in str(response.data)

    def test_password_reset_invalid_email_format(self, api_client):
        """Test password reset request with invalid email format."""
        url = reverse('password_reset')
        data = {"email": "invalid-email-format"}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'valid email' in str(response.data)

    def test_password_reset_inactive_user(self, api_client, inactive_user):
        """Test password reset request for inactive user."""
        url = reverse('password_reset')
        data = {"email": inactive_user.email}
        
        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1


    def test_password_reset_case_insensitive_email(self, api_client, user):
        """Test password reset with case-insensitive email."""
        url = reverse('password_reset')
        data = {"email": user.email.upper()}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]  
    
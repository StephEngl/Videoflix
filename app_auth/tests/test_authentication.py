import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status

User = get_user_model()


def make_login_request(api_client, email, password):
    """Helper function to make login requests."""
    url = reverse('login')
    data = {
        "email": email,
        "password": password,
    }
    return api_client.post(url, data, format='json')


def get_error_message(response_data):
    """Helper to extract error message from different DRF error formats."""
    if 'detail' in response_data:
        detail = response_data['detail']
        if isinstance(detail, list):
            return str(detail[0])
        return str(detail)
    
    if 'non_field_errors' in response_data:
        errors = response_data['non_field_errors']
        if isinstance(errors, list) and errors:
            return str(errors[0])
        return str(errors)
    
    return str(response_data)


@pytest.mark.django_db
class TestLoginView:
    """Test user login endpoint."""

    def test_successful_login(self, api_client, login_user):
        """Test successful user login."""
        response = make_login_request(api_client, login_user.email, "LoginPass123!")
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data 
        assert response.data['detail'] == "Login successful"
        assert 'user' in response.data
        assert 'id' in response.data['user']
        assert response.data['user']['username'] == login_user.username

        assert isinstance(response.data['detail'], str)
        assert isinstance(response.data['user'], dict)
        assert isinstance(response.data['user']['id'], int)
        assert isinstance(response.data['user']['username'], str)

    def test_login_wrong_password(self, api_client, login_user):
        """Test login fails with wrong password."""
        response = make_login_request(api_client, login_user.email, "WrongPassword123!")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_message = get_error_message(response.data)
        assert "Incorrect username or password" in error_message

    def test_login_inactive_user(self, api_client, inactive_user):
        """Test login fails for inactive user."""
        response = make_login_request(api_client, inactive_user.email, "testpass123")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error_message = get_error_message(response.data)
        assert "Incorrect username or password" in error_message

    def test_login_missing_fields(self, api_client):
        """Test login fails with missing fields."""
        url = reverse('login')
        response = api_client.post(url, {}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        response = api_client.post(url, {"email": "test@example.com"}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "password" in response.data or "This field is required" in str(response.data)
        
        response = api_client.post(url, {"password": "password123"}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "email" in response.data or "This field is required" in str(response.data)

def test_login_invalid_email_format(self, api_client):
    """Test login fails with invalid email format."""
    response = make_login_request(api_client, "invalid-email", "password123")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "email" in response.data or "valid email" in str(response.data)


@pytest.mark.django_db
class TestLogoutView:
    """Test user logout endpoint."""

    def test_logout(self, logged_in_api_client):
        """Test successful logout."""
        response = logged_in_api_client.post(reverse('logout'))
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data
        assert response.data['detail'] == "Logout successful! All tokens will be deleted. Refresh token is now invalid."
    
        assert isinstance(response.data['detail'], str)
    
    def test_logout_without_authentication(self, api_client):
        """Test logout fails without authentication."""
        response = api_client.post(reverse('logout'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'detail' in response.data
        assert "Authentication credentials were not provided" in str(response.data['detail'])



import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from test_helpers import make_activation_url


User = get_user_model()


@pytest.mark.django_db
class TestRegistrationView:
    """Test user registration endpoint."""
    
    def test_successful_registration(self, api_client):
        """Test successful user registration with activation email."""
        url = reverse('register')
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "confirmed_password": "SecurePass123!"
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'token' in response.data
        assert response.data['user']['email'] == "newuser@example.com"
        assert 'id' in response.data['user']

        assert isinstance(response.data['token'], str)
        assert isinstance(response.data['user'], dict)
        assert isinstance(response.data['user']['id'], int)
        assert isinstance(response.data['user']['email'], str)
        
        # Check user was created but is inactive
        user = User.objects.get(email="newuser@example.com")
        assert not user.is_active
        assert user.check_password("SecurePass123!")
        
        # Check activation email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["newuser@example.com"]
        assert "activate your videoflix account" in mail.outbox[0].subject.lower()

    def test_registration_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        url = reverse('register')
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "confirmed_password": "DifferentPass123!"
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirmed_password' in response.data

    def test_registration_duplicate_email(self, api_client, user):
        """Test registration with existing email - returns 201 but sends no email (anti-enumeration)."""
        url = reverse('register')
        data = {
            "email": user.email,
            "password": "SecurePass123!",
            "confirmed_password": "SecurePass123!"
        }
        mail.outbox.clear()
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'token' in response.data
        assert len(mail.outbox) == 0
    
        # Verify no new user was created
        user_count = User.objects.filter(email=user.email).count()
        assert user_count == 1

    def test_registration_invalid_email_security(self, api_client):
        """Test backend rejects invalid email (security test - frontend can be bypassed)."""
        url = reverse('register')
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "confirmed_password": "SecurePass123!"
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_registration_weak_password_security(self, api_client):
        """Test backend rejects weak passwords (security test)."""
        url = reverse('register')
        data = {
            "email": "test@example.com",
            "password": "123",
            "confirmed_password": "123"
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_registration_missing_fields(self, api_client):
        """Test registration fails with missing required fields."""
        url = reverse('register')
        data = {
            "email": "test@example.com"
            # missing password fields
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data


@pytest.mark.django_db
class TestActivateAccountView:
    """Test account activation endpoint."""
    
    def test_successful_activation(self, api_client, inactive_user):
        """Test successful account activation."""
        url = make_activation_url(inactive_user, valid_token=True)
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert "activation=success" in response.url or "success" in response.url
        
        inactive_user.refresh_from_db()
        assert inactive_user.is_active

    def test_activation_invalid_token(self, api_client, inactive_user):
        """Test activation fails with invalid token."""
        url = make_activation_url(inactive_user, valid_token=False)
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        inactive_user.refresh_from_db()
        assert not inactive_user.is_active

    def test_activation_invalid_uid(self, api_client, inactive_user):
        """Test activation fails with invalid uidb64."""
        url = make_activation_url(inactive_user, valid_token=False)
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        inactive_user.refresh_from_db()
        assert not inactive_user.is_active

    def test_activation_already_active_user(self, api_client, user):
        """Test activation of already active user."""
        assert user.is_active
        
        url = make_activation_url(user, valid_token=True)
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        user.refresh_from_db()
        assert user.is_active

    def test_activation_nonexistent_user(self, api_client):
        """Test activation fails for non-existent user."""
        non_existent_id = 99999
        assert not User.objects.filter(id=non_existent_id).exists()
        fake_user = User(id=99999)

        url = make_activation_url(fake_user, valid_token=False)

        user_count_before = User.objects.count()
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert "activation=failed" in response.url or "error" in response.url

        user_count_after = User.objects.count()
        assert user_count_before == user_count_after

        assert not User.objects.filter(id=non_existent_id).exists()


@pytest.mark.django_db
class TestRegistrationIntegration:
    """Integration tests for complete registration + activation flow."""
    
    def test_complete_registration_flow(self, api_client):
        """Test complete flow: register -> receive email -> activate."""
        # Step 1: Register user
        register_url = reverse('register')
        register_data = {
            "email": "integration@example.com",
            "password": "SecurePass123!",
            "confirmed_password": "SecurePass123!"
        }
        
        register_response = api_client.post(register_url, register_data, format='json')
        assert register_response.status_code == status.HTTP_201_CREATED
        
        user = User.objects.get(email="integration@example.com")
        assert not user.is_active
        
        # Step 2: Extract activation link from email
        assert len(mail.outbox) == 1
        
        # Step 3: Activate account (simulate clicking email link)
        activate_url = make_activation_url(user, valid_token=True)
        
        activate_response = api_client.get(activate_url)
        assert activate_response.status_code == status.HTTP_302_FOUND
        assert "activation=success" in activate_response.url or "success" in activate_response.url
        
        # Step 4: Verify user is now active
        user.refresh_from_db()
        assert user.is_active
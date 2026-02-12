import pytest
from django.core import mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestRegistrationView:
    """Test registration endpoint with activation email."""
    
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
    
    def test_successful_activation(self, api_client):
        """Test successful account activation."""
        # Create inactive user
        user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!",
            is_active=False
        )
        
        # Generate activation token and uid
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        url = reverse('activate-account', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == "Account successfully activated."
        
        # Check user is now active
        user.refresh_from_db()
        assert user.is_active

    def test_activation_invalid_token(self, api_client):
        """Test activation fails with invalid token."""
        user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!",
            is_active=False
        )
        
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = "invalid-token-123"
        
        url = reverse('activate-account', kwargs={
            'uidb64': uidb64,
            'token': invalid_token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # User should still be inactive
        user.refresh_from_db()
        assert not user.is_active

    def test_activation_invalid_uid(self, api_client):
        """Test activation fails with invalid uidb64."""
        user = User.objects.create_user(
            email="test@example.com",
            password="SecurePass123!",
            is_active=False
        )
        
        invalid_uidb64 = "invalid-uid"
        token = default_token_generator.make_token(user)
        
        url = reverse('activate-account', kwargs={
            'uidb64': invalid_uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_activation_nonexistent_user(self, api_client):
        """Test activation fails for non-existent user."""
        # Create valid looking uid for non-existent user
        fake_uid = urlsafe_base64_encode(force_bytes(99999))
        fake_token = "some-token"
        
        url = reverse('activate-account', kwargs={
            'uidb64': fake_uid,
            'token': fake_token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_activation_already_active_user(self, api_client, user):
        """Test activation of already active user."""
        # user fixture is already active
        assert user.is_active
        
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        url = reverse('activate-account', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        # Should still work but user remains active
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active


@pytest.mark.django_db
class TestRegistrationIntegration:
    """Integration tests for the complete registration flow."""
    
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
        email_body = mail.outbox[0].body
        
        # Step 3: Activate account (simulate clicking email link)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        activate_url = reverse('activate-account', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        activate_response = api_client.get(activate_url)
        assert activate_response.status_code == status.HTTP_200_OK
        assert activate_response.data['message'] == "Account successfully activated."
        
        # Step 4: Verify user is now active
        user.refresh_from_db()
        assert user.is_active
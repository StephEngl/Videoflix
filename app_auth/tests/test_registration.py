import pytest
from django.core import mail
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status

User = get_user_model()


def generate_activation_data(user):
    """Helper function to generate UID and token for user activation."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token


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
        user = inactive_user
        assert not user.is_active
        
        uidb64, token = generate_activation_data(user)
        
        url = reverse('activate', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert "activation=success" in response.url or "success" in response.url
        
        user.refresh_from_db()
        assert user.is_active

    def test_activation_invalid_token(self, api_client, inactive_user):
        """Test activation fails with invalid token."""
        user = inactive_user
        
        uidb64, _ = generate_activation_data(user)  # Valid UID, invalid token
        invalid_token = "invalid-token-123"
        
        url = reverse('activate', kwargs={
            'uidb64': uidb64,
            'token': invalid_token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        user.refresh_from_db()
        assert not user.is_active

    def test_activation_invalid_uid(self, api_client, inactive_user):
        """Test activation fails with invalid uidb64."""
        user = inactive_user
        
        invalid_uidb64 = "invalid-uid"
        token = default_token_generator.make_token(user)
        
        url = reverse('activate', kwargs={
            'uidb64': invalid_uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        user.refresh_from_db()
        assert not user.is_active

    def test_activation_already_active_user(self, api_client, user):
        """Test activation of already active user."""
        assert user.is_active
        
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        url = reverse('activate', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_302_FOUND
        user.refresh_from_db()
        assert user.is_active

    def test_activation_nonexistent_user(self, api_client):
        """Test activation fails for non-existent user."""
        non_existent_id = 99999
        assert not User.objects.filter(id=non_existent_id).exists()

        fake_uid = urlsafe_base64_encode(force_bytes(non_existent_id))
        fake_token = "some-token"
        
        url = reverse('activate', kwargs={
            'uidb64': fake_uid,
            'token': fake_token
        })

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
        email_body = mail.outbox[0].body
        
        # Step 3: Activate account (simulate clicking email link)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        activate_url = reverse('activate', kwargs={
            'uidb64': uidb64,
            'token': token
        })
        
        activate_response = api_client.get(activate_url)
        assert activate_response.status_code == status.HTTP_302_FOUND
        assert "activation=success" in activate_response.url or "success" in activate_response.url
        
        # Step 4: Verify user is now active
        user.refresh_from_db()
        assert user.is_active
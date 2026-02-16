from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def generate_activation_data(user, valid_token=True):
    """Helper function to generate UID and token for user activation/password reset."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    if valid_token:
        token = default_token_generator.make_token(user)
    else:
        token = "invalid-token-123"
    return uidb64, token


def make_activation_url(user, valid_token=True, url_name='activate'):
    """Helper function to generate activation/password reset URLs with tokens.
    
    Returns:
        str: Complete URL with uidb64 and token
    """
    uidb64, token = generate_activation_data(user, valid_token=valid_token)
    
    return reverse(url_name, kwargs={
        'uidb64': uidb64,
        'token': token
    })


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
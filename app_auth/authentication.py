from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication using HttpOnly cookies.
    
    Extracts JWT access token from request cookies instead of
    Authorization header for improved security.
    """
    def authenticate(self, request):
        access_token = request.COOKIES.get("access_token")
        if not access_token:
            return None
        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return user, validated_token
        except Exception as error:
            raise exceptions.AuthenticationFailed("Invalid token")
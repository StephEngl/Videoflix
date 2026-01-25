from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status, exceptions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import RegistrationSerializer, LoginSerializer
from ..services import EmailService, AuthService
from ..authentication import CookieJWTAuthentication


class RegistrationView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Send activation email via service
            token = EmailService.send_activation_email(user)

            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email
                },
                'token': token
            }, status=status.HTTP_201_CREATED)

        # Token als HTTP-ONLY Cookie setzen (später)
        # response.set_cookie('auth_token', token, httponly=True, secure=True)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        result = AuthService.activate_user(uidb64, token)

        if result['success']:
            return Response({'message': result['message']}, status=status.HTTP_200_OK)
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """POST /api/login/"""
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LogoutView(APIView):
    """POST /api/logout/"""
    """API view for user logout.
    
    Clears JWT tokens from HttpOnly cookies to securely
    log out the authenticated user.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = request.COOKIES.get("access_token")

        if not refresh_token and not access_token:
            return Response(
                {"error": "User is not logged in. No tokens found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {"detail": "Logout successful! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response
    

@extend_schema(
    tags=['Authentication'],
    description="Refresh JWT access token using the refresh token stored in HttpOnly cookie.",
    responses={
        200: {'detail': 'Token refreshed'},
        400: OpenApiResponse(description="Bad Request - Refresh token not provided."),
        401: OpenApiResponse(description="Unauthorized - Refresh token not provided or invalid"),
    }
)
class CookieTokenRefreshView(TokenRefreshView):
    """API view for refreshing JWT access tokens.
    
    Uses refresh token from HttpOnly cookies to generate new
    access token when the current one expires.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = self._get_refresh_token_from_cookies(request)
        
        if refresh_token is None:
            return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        access_token = self._validate_refresh_token(refresh_token)
        
        if access_token is None:
            return Response({"error": "Refresh token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)
        
        response = self._create_refresh_response(access_token)
        self._set_access_cookie(response, access_token)
        return response

    def _get_refresh_token_from_cookies(self, request):
        """Extract refresh token from HttpOnly cookies."""
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return None
        return refresh_token

    def _validate_refresh_token(self, refresh_token):
        """Validate refresh token and return new access token."""
        if refresh_token is None:
            return None
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data.get("access")
        except:
            return None

    def _create_refresh_response(self, access_token):
        """Create successful token refresh response."""
        data = {
            "detail": "Token refreshed",
            "access": access_token
        }
        return Response(data, status=status.HTTP_200_OK)

    def _set_access_cookie(self, response, access_token):
        """Set new access token as HttpOnly cookie."""
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
        )
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import redirect
from django.conf import settings
from .serializers import RegistrationSerializer, LoginSerializer, PasswordResetRequestSerializer
from ..services import EmailService, AuthService
from ..authentication import CookieJWTAuthentication


from app_auth.services import EmailService
from django.contrib.auth import get_user_model

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    description="Register a new user and send activation email.",
    responses={
        201: {'detail': 'Registration successful. Please check your email to activate your account.'},
        400: OpenApiResponse(description="Bad Request - Invalid input data"),
    }
)
class RegistrationView(APIView):
    """API view for user registration."""
    def post(self, request):
        """Register a new user and send activation email.
        
        Args:
            request: HTTP request containing user registration data.
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            EmailService.send_activation_email(user)
            return Response({'user': {'id': user.id, 'email': user.email}, 'message': 
                             'Registration successful. Please check your email to activate your account.'}, status=status.HTTP_201_CREATED)
        else:         
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    description="Activate user account via email link.",
    responses={
        200: {'message': 'Account successfully activated.'},
        400: OpenApiResponse(description="Bad Request - Invalid activation link"),
    }
) 
class ActivateAccountView(APIView):
    """API view for user account activation."""
    def get(self, request, uidb64, token):
        """Activate user account via email link.
        
        Args:
            request: HTTP request.
            uidb64: Base64 encoded user ID.
            token: Activation token.
            
        Returns:
            HttpResponseRedirect: Redirect to frontend with activation status.
        """
        result = AuthService.activate_user(uidb64, token)

        if result['success']:
            return redirect(f"{settings.FRONTEND_URL}?activation=success")
        else:
            return redirect(f"{settings.FRONTEND_URL}?activation=error")


@extend_schema(
    tags=['Authentication'],
    description="Obtain JWT tokens and set them in HttpOnly cookies.",
    responses={
        200: {'detail': 'Login successfully!'},
    }
)
class LoginView(APIView):
    """API view for user authentication."""
    def post(self, request):
        """Authenticate user and return JWT tokens.
        
        Args:
            request: HTTP request containing login credentials.
            
        Returns:
            Response: JWT tokens and user data or validation errors.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@extend_schema(
    tags=['Authentication'],
    description="Logout user by clearing JWT tokens from HttpOnly cookies.",
    responses={
        200: {'detail': 'Logout successful! All Tokens will be deleted. Refresh token is now invalid.'},
        400: OpenApiResponse(description="Bad Request - User is not logged in. No tokens found."),
    }
)
class LogoutView(APIView):
    """API view for user logout."""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout user by clearing JWT tokens from cookies.
            
        Returns:
            Response: Success message or error if no tokens found.
        """
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
    """API view for refreshing JWT access tokens using HttpOnly cookies."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Refresh access token using refresh token from cookies.
        
        Args:
            request: HTTP request containing refresh token in cookies.
            
        Returns:
            Response: New access token or error message.
        """
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
        """Extract refresh token from HttpOnly cookies.

        Returns:
            str or None: Refresh token if found, None otherwise.
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return None
        return refresh_token

    def _validate_refresh_token(self, refresh_token):
        """Validate refresh token and return new access token.
        
        Args:
            refresh_token: JWT refresh token.
            
        Returns:
            str or None: New access token if valid, None otherwise.
        """
        if refresh_token is None:
            return None
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
            return serializer.validated_data.get("access")
        except:
            return None

    def _create_refresh_response(self, access_token):
        """Create successful token refresh response.
        
        Args:
            access_token: New JWT access token.
            
        Returns:
            Response: Response containing new access token.
        """
        data = {
            "detail": "Token refreshed",
            "access": access_token
        }
        return Response(data, status=status.HTTP_200_OK)

    def _set_access_cookie(self, response, access_token):
        """Set new access token as HttpOnly cookie.
        
        Args:
            response: HTTP response object.
            access_token: JWT access token to set in cookie.
        """
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
        )

@extend_schema(
    tags=['Authentication'],
    description="Request password reset email.",
    responses={
        200: {'detail': 'An email has been sent to reset your password.'},
        400: OpenApiResponse(description="Bad Request - Invalid input data"),
    }
)
class PasswordResetView(APIView):
    """API view for password reset request."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Send password reset email.
        
        Args:
            request: HTTP request containing user email.
            
        Returns:
            Response: Success message or validation errors.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            EmailService.send_password_reset_email(email)
            return Response(
                {'detail': 'An email has been sent to reset your password.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
@extend_schema(
    tags=['Authentication'],
    description="Confirm password reset with new password.",
    responses={
        200: {'detail': 'Your Password has been successfully reset.'},
        400: OpenApiResponse(description="Bad Request - Invalid token or input data"),
    }
)
class PasswordConfirmView(APIView):
    """API view for password reset confirmation."""
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Confirm password reset with new password.
        
        Args:
            request: HTTP request containing new password.
            uidb64: Base64 encoded user ID.
            token: Password reset token.
        """
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = AuthService.reset_password(uidb64, token, new_password)
        if result['success']:
            return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
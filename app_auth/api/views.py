from rest_framework import status, exceptions
from rest_framework.permissions import IsAuthenticated
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
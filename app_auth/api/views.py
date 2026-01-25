from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegistrationSerializer, LoginSerializer
from .services import EmailService

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


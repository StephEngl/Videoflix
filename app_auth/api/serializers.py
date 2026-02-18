from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation.
    
    Handles user registration including email validation, password confirmation,
    and automatic username generation from email.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 8,
                'error_messages': {
                    'min_length': 'Password must be at least 8 characters long.',
                    'required': 'Password is required.',
                    'blank': 'Password cannot be blank.'
                    }
                },
            'email': {
                'required': True,
                'allow_blank': False,
                'error_messages': {
                    'invalid': 'Enter a valid email address.',
                    'required': 'Email address is required.'
                    }
                },
        }

    def validate_confirmed_password(self, value):
        """Validate that confirmed password matches the password field.
           
        Returns:
            str: The validated confirmed password.
            
        Raises:
            ValidationError: If passwords do not match.
        """
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        """Validate and normalize email format.
    
        Note: Email uniqueness is NOT checked here to prevent enumeration attacks.
        Duplicate handling occurs silently in the create() method.
        """
        if not value:
            raise serializers.ValidationError("Email is required.")
    
        normalized_email = value.lower()

        return normalized_email

    def create(self, validated_data):
        """Create a new inactive user with auto-generated username.
        
        If email already exists, we silently 'succeed' to prevent enumeration.
        The existing user will receive an email indicating someone tried to register.
          
        Returns:
            User: The created or existing user instance.
        """
        validated_data.pop('confirmed_password')
        email = validated_data['email']
        
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            return existing_user
        
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            is_active=False
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """JWT token serializer for email-based authentication.
    
    Extends TokenObtainPairSerializer to allow login with email instead of username.
    """
    email = serializers.EmailField()
    password = serializers.CharField()

    def __init__(self, *args, **kwargs):
        """Initialize serializer with email field instead of username."""
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = serializers.EmailField()
    
    def validate(self, attrs):
        """Validate email/password and convert to username for JWT token generation.
            
        Returns:
            dict: Validated data with JWT tokens and user info.
        """
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            try:
                user = User.objects.get(email=email)
                attrs['username'] = user.username
                attrs.pop('email')
            except User.DoesNotExist:
                raise serializers.ValidationError("Incorrect username or password.")

        try:
            data = super().validate(attrs)
            data['detail'] = 'Login successful'
            data['user'] = self.get_user_data()
            return data
        except Exception:
            raise serializers.ValidationError("Incorrect username or password.")
        
    def get_user_data(self):
        """Get formatted user data for the response.
        """
        return {
            "id": self.user.pk,
            "username": self.user.username,
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate and normalize email format."""
        normalized_email = (value or "").strip().lower()
        
        if not normalized_email:
            raise serializers.ValidationError("Email is required.")
            
        return normalized_email


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validate that new passwords match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    """User registration with password confirmation."""
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def create(self, validated_data):
        validated_data.pop('confirmed_password')
        
        # Generate username from email
        email = validated_data['email']
        base_username = email.split('@')[0]
        
        # Ensure username is unique
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create inactive user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=validated_data['password'],
            is_active=False
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """JWT token serializer with email login - converts email to username."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Delete username field as we use email for login
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = serializers.EmailField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            try:
                user = User.objects.get(email=email)
                # Username für super().validate() setzen
                attrs['username'] = user.username
                attrs.pop('email')  # Email entfernen, da super() nur username kennt
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
        """Get formatted user data for the response."""
        return {
            "id": self.user.pk,
            "username": self.user.username,
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
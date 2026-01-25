from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailService:
    @staticmethod
    def send_activation_email(user):
        """Send activation email to user."""
        # Generate activation token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        
        # Render HTML template
        html_content = render_to_string('app_auth/confirm_email.html', {
            'username': user.username,
            'activation_link': activation_link,
        })
        
        # Plain text fallback
        text_content = f"""
        Dear {user.username},
        
        Thank you for registering at Videoflix!
        Please click the following link to verify your email address and complete your registration:
        {activation_link}
        
        If you didn't create this account, please disregard this email.
        
        Best regards,
        Your Videoflix Team
        """
        
        # Send email
        email_message = EmailMultiAlternatives(
            subject="Activate your Videoflix account",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)
        
        return token
    

class AuthService:
    @staticmethod
    def activate_user(uidb64, token):
        """Activate user account with token validation."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return {'success': True, 'message': 'Account activated successfully!'}
            else:
                return {'success': False, 'error': 'Invalid activation link.'}
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return {'success': False, 'error': 'Invalid activation link.'}
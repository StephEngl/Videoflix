from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from email.mime.image import MIMEImage
import os

User = get_user_model()

class EmailService:
    """Service for sending authentication-related emails."""
    
    @staticmethod
    def send_email(user, subject, text_template, html_template, link):
        """Send templated email with embedded logo.
        
        Args:
            user: User object to send email to.
            subject: Email subject line.
            text_template: Path to plain text template.
            html_template: Path to HTML template.
            link: Complete URL link for the email.
        """
        logo_cid = "logo"
        context = {
            'username': user.username,
            'activation_link': link,
            'reset_password_link': link,
            'logo_cid': logo_cid,
        }
        
        text_content = render_to_string(text_template, context)
        html_content = render_to_string(html_template, context)
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        EmailService.attach_logo_to_email(email_message, logo_cid)
        email_message.send(fail_silently=False)

    @staticmethod
    def send_activation_email(user):
        """Send account activation email only for new inactive users.
        
        Args:
            user: User object to send activation email to.
            
        Returns:
            str: Generated activation token.
        """
        if not user.is_active:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link = f"{getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500')}/pages/auth/activate.html?uid={uid}&token={token}"
            
            EmailService.send_email(
                user=user,
                subject="Activate your Videoflix account",
                text_template='confirm_email.txt',
                html_template='confirm_email.html',
                link=link
            )
            return token
        return None

    @staticmethod
    def send_password_reset_email(email):
        """Send password reset email if user exists with case-insensitive lookup.
    
        Args:
            email: Email address to send password reset to.
            include_activation: Whether to mention account activation in message.
            
        Returns:
            dict: Contains success status, message, and whether user was found.
        """
        try:
            user = User.objects.get(email__iexact=email.strip())
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            link = f"{getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500')}/pages/auth/confirm_password.html?uid={uid}&token={token}"
            
            if not user.is_active:
                subject = "Activate and reset your Videoflix password"
            else:
                subject="Reset your Videoflix password"
            
            EmailService.send_email(
                user=user,
                subject=subject,
                text_template='forgot_password.txt',
                html_template='forgot_password.html',
                link=link
            )
            return token
        except User.DoesNotExist:
            # Don't reveal if email exists for security reasons
            return None

    @staticmethod
    def attach_logo_to_email(email_message, logo_cid):
        """Attach logo image to email message for embedding.
        
        Args:
            email_message: EmailMultiAlternatives object.
            logo_cid: Content ID for the logo image.
        """
        logo_path = os.path.join(settings.BASE_DIR, 'app_auth', 'assets', 'logo_icon.svg')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            
            logo_image = MIMEImage(logo_data, _subtype='svg+xml')
            logo_image.add_header('Content-ID', f'<{logo_cid}>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo.svg')
            email_message.attach(logo_image)
    

class AuthService:
    """Service for user authentication operations."""
    
    @staticmethod
    def activate_user(uidb64, token):
        """Activate user account with token validation.
        
        Args:
            uidb64: Base64 encoded user ID.
            token: Activation token.
            
        Returns:
            dict: Success status and message or error.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return {'success': True, 'message': 'Account successfully activated.'}
            else:
                return {'success': False, 'error': 'Invalid activation link.'}
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return {'success': False, 'error': 'Invalid activation link.'}
    
    @staticmethod
    def reset_password(uidb64, token, new_password):
        """Reset user password with token validation and auto-activation.
        
        Args:
            uidb64: Base64 encoded user ID.
            token: Password reset token.
            new_password: New password to set.
            
        Returns:
            dict: Success status and message or error.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)

                if not user.is_active:
                    user.is_active = True

                user.save()
                
                return {'success': True, 'detail': 'Your Password has been successfully reset.'}
            else:
                return {'success': False, 'error': 'Invalid password reset link.'}
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return {'success': False, 'error': 'Invalid password reset link.'}
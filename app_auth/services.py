from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
# from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from email.mime.image import MIMEImage
import os

User = get_user_model()

class EmailService:
    @staticmethod
    def send_email(user, subject, text_template, html_template, url_pattern):
        """
        Central function to send emails with token-based links.
        
        Args:
            user: User object
            subject: Email subject line
            text_template: Plain text template name
            html_template: HTML template name  
            url_pattern: URL pattern with placeholders for uid and token
        """
        # Generate token and uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        link = f"{getattr(settings, 'BACKEND_URL', 'http://localhost:8000')}{url_pattern.format(uid=uid, token=token)}"
        
        # Content ID for embedded logo
        logo_cid = "logo"
        context = {
            'username': user.username,
            'activation_link': link,  # Keep as activation_link for template compatibility
            'reset_link': link,       # Keep as reset_link for template compatibility
            'logo_cid': logo_cid,
        }
        
        # Render templates
        text_content = render_to_string(text_template, context)
        html_content = render_to_string(html_template, context)
        
        # Create email message
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        EmailService.attach_logo_to_email(email_message, logo_cid)
        
        email_message.send(fail_silently=False)
        
        return token

    @staticmethod
    def send_activation_email(user):
        """Send activation email to user."""
        return EmailService.send_email(
            user=user,
            subject="Activate your Videoflix account",
            text_template='confirm_email.txt',
            html_template='confirm_email.html',
            url_pattern="/api/activate/{uid}/{token}/"
        )

    @staticmethod
    def send_password_reset_email(email):
        """Send password reset email if user exists."""
        try:
            user = User.objects.get(email=email)
            return EmailService.send_email(
                user=user,
                subject="Reset your Videoflix password",
                text_template='forgot_password.txt',
                html_template='forgot_password.html',
                url_pattern="/api/password_reset/{uid}/{token}/"
            )
        except User.DoesNotExist:
            # Don't reveal if email exists for security reasons
            return None

    @staticmethod
    def attach_logo_to_email(email_message, logo_cid):
        """Attach logo image to email message."""
        logo_path = os.path.join(settings.BASE_DIR, 'app_auth', 'assets', 'logo_icon.svg')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            
            logo_image = MIMEImage(logo_data, _subtype='svg+xml')
            logo_image.add_header('Content-ID', f'<{logo_cid}>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo.svg')
            email_message.attach(logo_image)
    

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
                return {'success': True, 'message': 'Account successfully activated.'}
            else:
                return {'success': False, 'error': 'Invalid activation link.'}
                
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return {'success': False, 'error': 'Invalid activation link.'}
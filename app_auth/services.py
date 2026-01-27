from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from email.mime.image import MIMEImage
import os

User = get_user_model()

class EmailService:
    @staticmethod
    def send_activation_email(user):
        """Send activation email to user."""
        # Generate activation token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        
        # Content ID for embedded logo
        logo_cid = "logo"
        
        context = {
            'username': user.username,
            'activation_link': activation_link,
            'logo_cid': logo_cid,
            'base_url': settings.FRONTEND_URL,
        }

         # Plain text fallback
        text_content = render_to_string('confirm_email.txt', context)

        # Render HTML template
        html_content = render_to_string('confirm_email.html', context)
        
        # Create email message
        email_message = EmailMultiAlternatives(
            subject="Activate your Videoflix account",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_message.attach_alternative(html_content, "text/html")
        
        EmailService.attach_logo_to_email(email_message, logo_cid)
        
        email_message.send(fail_silently=False)
        
        return token

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
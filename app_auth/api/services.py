from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

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
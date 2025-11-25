"""
Custom email backend for SendGrid using Web API (faster and more reliable than SMTP)
"""
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Content

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """
    SendGrid email backend using Web API instead of SMTP.
    This is faster and more reliable, preventing worker timeouts.
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError('SENDGRID_API_KEY must be set in settings')
            logger.warning('SENDGRID_API_KEY not set, email sending will fail')
        else:
            self.sg = SendGridAPIClient(self.api_key)
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of emails sent.
        """
        if not email_messages:
            return 0
        
        num_sent = 0
        for message in email_messages:
            try:
                self._send(message)
                num_sent += 1
            except Exception as e:
                if not self.fail_silently:
                    logger.error(f"Failed to send email via SendGrid: {str(e)}", exc_info=True)
                    raise
                else:
                    logger.warning(f"Failed to send email via SendGrid (fail_silently=True): {str(e)}")
        
        return num_sent
    
    def _send(self, email_message):
        """Send a single email message using SendGrid API"""
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError('SENDGRID_API_KEY not configured')
            return
        
        # Get from email
        from_email = email_message.from_email or settings.DEFAULT_FROM_EMAIL
        
        # Create SendGrid Mail object
        mail = Mail(
            from_email=Email(from_email),
            to_emails=email_message.to,
            subject=email_message.subject,
        )
        
        # Add content (prefer HTML if available)
        if email_message.body:
            if hasattr(email_message, 'alternatives') and email_message.alternatives:
                # HTML email
                html_content = None
                text_content = email_message.body
                for content, mimetype in email_message.alternatives:
                    if mimetype == 'text/html':
                        html_content = content
                        break
                
                if html_content:
                    mail.add_content(Content("text/html", html_content))
                    mail.add_content(Content("text/plain", text_content))
                else:
                    mail.add_content(Content("text/plain", text_content))
            else:
                # Plain text only
                mail.add_content(Content("text/plain", email_message.body))
        
        # Add reply-to if specified
        if email_message.reply_to:
            mail.reply_to = Email(email_message.reply_to[0])
        
        # Send the email
        try:
            response = self.sg.send(mail)
            logger.info(f"Email sent successfully via SendGrid. Status: {response.status_code}")
            if response.status_code not in [200, 201, 202]:
                logger.warning(f"SendGrid returned non-success status: {response.status_code}")
        except Exception as e:
            logger.error(f"SendGrid API error: {str(e)}", exc_info=True)
            raise


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
            print('[SendGrid] WARNING: SENDGRID_API_KEY not set, email sending will fail')
        else:
            try:
                self.sg = SendGridAPIClient(self.api_key)
                logger.info('SendGrid backend initialized successfully')
                print('[SendGrid] Backend initialized successfully')
            except Exception as e:
                logger.error(f'Failed to initialize SendGrid client: {str(e)}', exc_info=True)
                print(f'[SendGrid] ERROR: Failed to initialize SendGrid client: {str(e)}')
                if not self.fail_silently:
                    raise
    
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
            logger.error('SENDGRID_API_KEY not configured, cannot send email')
            return
        
        # Get from email
        from_email = email_message.from_email or settings.DEFAULT_FROM_EMAIL
        
        # Ensure to_emails is a list
        to_emails = email_message.to
        if not isinstance(to_emails, list):
            to_emails = [to_emails] if to_emails else []
        
        if not to_emails:
            error_msg = "No recipient email address provided"
            logger.error(error_msg)
            print(f"[SendGrid] ERROR: {error_msg}")
            if not self.fail_silently:
                raise ValueError(error_msg)
            return
        
        # Log email attempt
        logger.info(f"Attempting to send email via SendGrid to: {to_emails}, subject: {email_message.subject}")
        print(f"[SendGrid] Sending email to: {to_emails}, subject: {email_message.subject}, from: {from_email}")
        
        # Create SendGrid Mail object
        mail = Mail(
            from_email=Email(from_email),
            to_emails=to_emails,
            subject=email_message.subject,
        )
        
        # Add content (prefer HTML if available)
        html_content = None
        text_content = email_message.body or ''
        
        # Check for HTML in alternatives
        if hasattr(email_message, 'alternatives') and email_message.alternatives:
            for content, mimetype in email_message.alternatives:
                if mimetype == 'text/html':
                    html_content = content
                    break
        
        # Add content to mail
        if html_content:
            mail.add_content(Content("text/html", html_content))
            mail.add_content(Content("text/plain", text_content or 'This email requires HTML support.'))
            logger.info(f"Email has both HTML and plain text content")
        elif text_content:
            mail.add_content(Content("text/plain", text_content))
            logger.info(f"Email has plain text content only")
        else:
            logger.warning(f"Email has no content, using default")
            mail.add_content(Content("text/plain", "No content provided"))
        
        # Add reply-to if specified
        if email_message.reply_to:
            mail.reply_to = Email(email_message.reply_to[0])
        
        # Send the email
        try:
            response = self.sg.send(mail)
            status_code = response.status_code
            logger.info(f"Email sent successfully via SendGrid. Status: {status_code}")
            print(f"[SendGrid] Email sent successfully! Status: {status_code}")
            
            if status_code not in [200, 201, 202]:
                error_msg = f"SendGrid returned non-success status: {status_code}"
                logger.warning(error_msg)
                print(f"[SendGrid] WARNING: {error_msg}")
                # Get response body if available
                try:
                    body = response.body
                    logger.warning(f"SendGrid response body: {body}")
                    print(f"[SendGrid] Response body: {body}")
                except:
                    pass
        except Exception as e:
            error_msg = f"SendGrid API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"[SendGrid] ERROR: {error_msg}")
            if not self.fail_silently:
                raise
            else:
                logger.warning(f"Failed to send email via SendGrid (fail_silently=True): {str(e)}")


"""
Django management command to test email sending via SendGrid
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email sending via SendGrid'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            required=True,
            help='Email address to send test email to',
        )

    def handle(self, *args, **options):
        to_email = options['to']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Testing Email Configuration'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Check configuration
        self.stdout.write(f'\nEmail Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Default From Email: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'SendGrid API Key: {"Set" if getattr(settings, "SENDGRID_API_KEY", None) else "Not Set"}')
        
        # Test email
        subject = 'Test Email from Ripple'
        message = 'This is a test email to verify SendGrid configuration.'
        html_message = '<html><body><h1>Test Email</h1><p>This is a test email to verify SendGrid configuration.</p></body></html>'
        
        self.stdout.write(f'\nSending test email to: {to_email}')
        self.stdout.write(f'Subject: {subject}')
        
        try:
            result = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                fail_silently=False,
                html_message=html_message,
            )
            self.stdout.write(self.style.SUCCESS(f'\n✓ Email sent successfully!'))
            self.stdout.write(f'  Result: {result} (1 = success, 0 = failure)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Failed to send email:'))
            self.stdout.write(self.style.ERROR(f'  {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(f'\n{traceback.format_exc()}'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))


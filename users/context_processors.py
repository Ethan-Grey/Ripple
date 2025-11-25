# users/context_processors.py
from django.conf import settings

def recaptcha_site_key(request):
    """
    Add reCAPTCHA site key to all template contexts.
    This allows you to use {{ RECAPTCHA_SITE_KEY }} in any template.
    """
    return {
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }
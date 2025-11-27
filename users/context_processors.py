# users/context_processors.py
from django.conf import settings

def recaptcha_site_key(request):
    """
    Add reCAPTCHA site key to all template contexts.
    This allows you to use {{ RECAPTCHA_SITE_KEY }} in any template.
    """
    return {
        'RECAPTCHA_SITE_KEY': getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    }

def unread_messages_count(request):
    """
    Add unread message count to all template contexts.
    This allows you to use {{ unread_messages_count }} in any template.
    """
    unread_count = 0
    if request.user.is_authenticated:
        from chat.models import MessageStatus
        unread_count = MessageStatus.objects.filter(
            user=request.user,
            is_read=False
        ).exclude(
            message__sender=request.user
        ).count()
    
    return {
        'unread_messages_count': unread_count
    }
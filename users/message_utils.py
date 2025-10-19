"""
Utility functions for handling Django messages in different contexts
"""
from django.contrib import messages

def clear_unrelated_messages(request, allowed_tags=None):
    """
    Clear messages that are not relevant to the current context.
    
    Args:
        request: Django request object
        allowed_tags: List of message tags to keep (e.g., ['error', 'warning'])
    """
    if allowed_tags is None:
        allowed_tags = ['error', 'warning']
    
    # Get all messages and filter them
    all_messages = list(messages.get_messages(request))
    messages_to_keep = []
    
    for message in all_messages:
        # Keep error and warning messages, but filter out success/info messages
        if message.level_tag in allowed_tags:
            messages_to_keep.append(message)
    
    # Clear all messages
    list(messages.get_messages(request))
    
    # Re-add only the messages we want to keep
    for message in messages_to_keep:
        if message.level_tag == 'error':
            messages.error(request, message.message)
        elif message.level_tag == 'warning':
            messages.warning(request, message.message)
        elif message.level_tag == 'info':
            messages.info(request, message.message)
        elif message.level_tag == 'success':
            messages.success(request, message.message)

def clear_all_messages(request):
    """Clear all messages from the request"""
    list(messages.get_messages(request))

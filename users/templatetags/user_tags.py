from django import template
import hashlib

register = template.Library()

# Color palette for avatar backgrounds
AVATAR_COLORS = [
    '#667eea',  # Purple
    '#764ba2',  # Deep purple
    '#f093fb',  # Pink
    '#4facfe',  # Blue
    '#00f2fe',  # Cyan
    '#43e97b',  # Green
    '#fa709a',  # Rose
    '#fee140',  # Yellow
    '#30cfd0',  # Teal
    '#a8edea',  # Mint
    '#ff9a9e',  # Coral
    '#fecfef',  # Light pink
    '#fad961',  # Gold
    '#c471ed',  # Violet
    '#12c2e9',  # Sky blue
]


def get_avatar_color(user):
    """Generate a consistent color for a user based on their username"""
    # Use username to generate a consistent hash
    hash_value = int(hashlib.md5(user.username.encode()).hexdigest(), 16)
    color_index = hash_value % len(AVATAR_COLORS)
    return AVATAR_COLORS[color_index]


@register.inclusion_tag('users/user_avatar.html', takes_context=False)
def user_avatar(user, size='medium', css_class=''):
    """
    Display user avatar with fallback to initials
    
    Usage: {% user_avatar user %}
           {% user_avatar user size='large' %}
           {% user_avatar user css_class='custom-class' %}
    """
    has_avatar = user.profile.avatar if hasattr(user, 'profile') else False
    
    # Get initials from first and last name, or fallback to username
    first_name = user.first_name or ''
    last_name = user.last_name or ''
    
    if first_name and last_name:
        initials = f"{first_name[0]}{last_name[0]}".upper()
    elif first_name:
        initials = first_name[0].upper()
    elif last_name:
        initials = last_name[0].upper()
    else:
        # Fallback to username
        initials = user.username[0].upper() if user.username else '?'
    
    avatar_color = get_avatar_color(user)
    
    return {
        'user': user,
        'has_avatar': has_avatar,
        'avatar_url': user.profile.avatar.url if has_avatar else None,
        'initials': initials,
        'avatar_color': avatar_color,
        'size': size,
        'css_class': css_class,
    }


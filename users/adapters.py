from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to handle social account signups without email verification"""
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow automatic signup for social accounts"""
        return True
        
    def populate_user(self, request, sociallogin, data):
        """Populate user data from social account"""
        user = super().populate_user(request, sociallogin, data)
        if sociallogin.account.provider == 'google':
            # Generate username from email if not provided
            if not user.username and data.get('email'):
                base_username = data.get('email').split('@')[0]
                username = base_username
                User = get_user_model()
                
                # If username is taken, append a number
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user.username = username
        return user
        
    def pre_social_login(self, request, sociallogin):
        """Handle connecting existing accounts"""
        # If email exists, connect the account to the existing user
        if sociallogin.email_addresses:
            email_address = sociallogin.email_addresses[0]
            User = get_user_model()
            try:
                user = User.objects.get(email=email_address.email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
        return super().pre_social_login(request, sociallogin)
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors by redirecting to login page"""
        from django.contrib import messages
        messages.info(request, 'Social login was cancelled or failed. Please try again.')
        raise ImmediateHttpResponse(redirect(reverse('users:login')))
        
    def save_user(self, request, sociallogin, form=None):
        """Save user and automatically verify email for social accounts"""
        user = super().save_user(request, sociallogin, form)
        
        # Automatically verify email for social accounts
        if sociallogin.account.provider == 'google' and user.email:
            # Create or update EmailAddress with verified=True
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={
                    'verified': True,
                    'primary': True
                }
            )
            # If email address already exists, mark it as verified
            if not created:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter for regular account signups"""
    
    def get_signup_redirect_url(self, request):
        """Redirect after signup"""
        from django.urls import reverse
        return reverse('core:home')
        
    def get_login_redirect_url(self, request):
        """Redirect after login"""
        from django.urls import reverse
        return reverse('core:home')
        
    def is_open_for_signup(self, request):
        """Allow signups"""
        return True
    
    def is_active_for_authentication(self, user):
        """Check if user is active - allauth will redirect to /accounts/inactive/ if False"""
        # Return False to let allauth handle the redirect to /accounts/inactive/
        # We've overridden that URL to point to our custom suspended page
        return user.is_active


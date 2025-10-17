from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django import forms
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib import messages

# Create your views here.

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Get form data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email_value = request.POST.get('email', '').strip()
            
            # Validate email is provided
            if not email_value:
                messages.error(request, 'Email is required for registration.')
                return render(request, 'register.html', {'form': form})
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email_value)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return render(request, 'register.html', {'form': form})
            
            # Check if email already exists
            if User.objects.filter(email=email_value).exists():
                messages.error(request, 'This email is already registered. Please use a different email or sign in.')
                return render(request, 'register.html', {'form': form})
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username is already taken. Please choose a different one.')
                return render(request, 'register.html', {'form': form})
            
            # Store data in session for verification
            request.session['user_data'] = {
                'username': username,
                'password': password,
                'email': email_value,
            }
            request.session.modified = True
            
            # Generate verification token
            token = default_token_generator.make_token(User(username=username))
            uid = urlsafe_base64_encode(force_bytes(username))
            
            verification_url = request.build_absolute_uri(
                f'/verify-email/{uid}/{token}/'
            )
            
            # Send verification email
            subject = 'Verify your email address - Ripple'
            message = render_to_string('email_verification.html', {
                'username': username,
                'verification_url': verification_url,
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email_value],
                fail_silently=False,
            )
            
            return render(request, 'registration_success.html', {
                'email': email_value
            })
    else:
        form = UserCreationForm()
    # Add email field dynamically for a simple UX
    if not hasattr(form.fields, 'email'):
        form.fields['email'] = forms.EmailField(required=True, label='Email')
    return render(request, 'register.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        username = force_str(urlsafe_base64_decode(uidb64))
        user_data = request.session.get('user_data')
        
        if not user_data or user_data['username'] != username:
            return render(request, 'email_verification_failed.html')
            
        # Create the user only after email verification
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password']
        )
        
        # Clean up session data
        if 'user_data' in request.session:
            del request.session['user_data']
            
        return render(request, 'email_verification_success.html')
        
    except Exception as e:
        print(f"Error in email verification: {e}")
        return render(request, 'email_verification_failed.html')


def logout_direct(request):
    auth_logout(request)
    return redirect('users:login')

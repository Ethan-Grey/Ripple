from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
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
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.dispatch import receiver
from django.contrib.auth.signals import user_login_failed
import logging
from .models import Profile, Evidence, IdentitySubmission
from skills.models import UserSkill, Skill, SkillEvidence, TeachingClass, TeacherApplication, ClassEnrollment
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from .message_utils import clear_all_messages
from communities.models import CommunityRequest
import requests  # For reCAPTCHA verification

logger = logging.getLogger(__name__)

# Signal to capture login attempts for inactive users
@receiver(user_login_failed)
def capture_inactive_login_attempt(sender, credentials, request, **kwargs):
    """Capture login attempts for inactive users and store username in session"""
    username = credentials.get('username') or credentials.get('email')
    if username:
        try:
            from django.db.models import Q
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if user and not user.is_active:
                # Store user info in session for suspended page
                request.session['suspended_user_id'] = user.id
                request.session['suspended_username'] = user.username
        except Exception:
            pass

# Create your views here.

def verify_recaptcha(recaptcha_response):
    """Verify reCAPTCHA with Google"""
    if not recaptcha_response:
        return False
    
    url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': recaptcha_response
    }
    
    try:
        response = requests.post(url, data=data, timeout=5)
        result = response.json()
        return result.get('success', False)
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        return False


def custom_login(request):
    """Custom login view with reCAPTCHA validation"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    # Clear all existing messages to prevent showing unrelated messages
    clear_all_messages(request)
    
    if request.method == 'POST':
        # Verify reCAPTCHA first
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            form = AuthenticationForm(data=request.POST)
            return render(request, 'users/login.html', {'form': form})
        
        # Proceed with authentication if reCAPTCHA is valid
        form = AuthenticationForm(data=request.POST)
        
        # Check for inactive user before form validation
        username = request.POST.get('username')
        if username:
            try:
                # Try to find user by username or email
                from django.db.models import Q
                user = User.objects.filter(
                    Q(username=username) | Q(email=username)
                ).first()
                
                if user and not user.is_active:
                    # Find the most recent suspension report
                    from core.models import Report
                    from django.contrib.contenttypes.models import ContentType
                    
                    user_content_type = ContentType.objects.get_for_model(user)
                    suspension_report = Report.objects.filter(
                        content_type=user_content_type,
                        object_id=user.id,
                        action_taken__in=['user_suspended', 'user_banned']
                    ).order_by('-created_at').first()
                    
                    suspension_reason = None
                    admin_notes = None
                    
                    if suspension_report:
                        # Get the reason from the report
                        suspension_reason = suspension_report.get_reason_display()
                        if suspension_report.admin_notes:
                            admin_notes = suspension_report.admin_notes
                    
                    # If no report found, use default message
                    if not suspension_reason:
                        suspension_reason = "Your account has been suspended for violating our community guidelines."
                    
                    return render(request, 'users/account_suspended.html', {
                        'suspension_reason': suspension_reason,
                        'admin_notes': admin_notes
                    })
            except (User.DoesNotExist, Exception):
                pass  # Let form handle the error
        
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Handle "remember me" checkbox
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            
            # Redirect to next URL or home
            next_url = request.GET.get('next', 'core:home')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def account_suspended(request):
    """View for suspended account page"""
    # Find the most recent suspension report for the user
    from core.models import Report
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    
    suspension_reason = None
    admin_notes = None
    user = None
    
    # Try to get user from various sources
    # 1. From authenticated user (if somehow logged in but inactive)
    if request.user.is_authenticated and not request.user.is_active:
        user = request.user
    # 2. From URL parameter (passed by adapter)
    elif request.GET.get('user_id'):
        try:
            user = User.objects.get(id=request.GET.get('user_id'))
        except (User.DoesNotExist, ValueError):
            pass
    # 3. Try to get from username/email in POST data (from login form)
    elif request.method == 'POST' and 'login' in request.POST:
        username = request.POST.get('login')
        if username:
            try:
                user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            except User.DoesNotExist:
                pass
    # 4. Try to get from username in GET parameter
    elif request.GET.get('username'):
        try:
            username = request.GET.get('username')
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        except User.DoesNotExist:
            pass
    # 5. Try to get from suspended user info in session (set by adapter)
    elif 'suspended_user_id' in request.session:
        try:
            user = User.objects.get(id=request.session.get('suspended_user_id'))
            # Clear the session data after use
            del request.session['suspended_user_id']
            if 'suspended_username' in request.session:
                del request.session['suspended_username']
        except (User.DoesNotExist, ValueError):
            pass
    # 6. Try to get from username in session
    elif 'username' in request.session:
        try:
            user = User.objects.get(username=request.session.get('username'))
        except User.DoesNotExist:
            pass
    
    if user and not user.is_active:
        user_content_type = ContentType.objects.get_for_model(user)
        suspension_report = Report.objects.filter(
            content_type=user_content_type,
            object_id=user.id,
            action_taken__in=['user_suspended', 'user_banned']
        ).order_by('-created_at').first()
        
        if suspension_report:
            suspension_reason = suspension_report.get_reason_display()
            if suspension_report.admin_notes:
                admin_notes = suspension_report.admin_notes
    
    # If no report found, use default message
    if not suspension_reason:
        suspension_reason = "Your account has been suspended for violating our community guidelines."
    
    return render(request, 'users/account_suspended.html', {
        'suspension_reason': suspension_reason,
        'admin_notes': admin_notes
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    
    # Clear all existing messages to prevent showing unrelated messages
    clear_all_messages(request)
    
    if request.method == 'POST':
        # Check agree_terms checkbox FIRST
        if not request.POST.get('agree_terms'):
            messages.error(request, 'You must agree to the Terms of Service and Privacy Policy to register.')
            form = UserCreationForm(request.POST)
            return render(request, 'users/register.html', {'form': form})
        
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Get form data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email_value = request.POST.get('email', '').strip()
            
            # Validate email is provided
            if not email_value:
                messages.error(request, 'Email is required for registration.')
                return render(request, 'users/register.html', {'form': form})
            
            # Validate email format
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(email_value)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return render(request, 'users/register.html', {'form': form})
            
            # Check if email already exists
            if User.objects.filter(email=email_value).exists():
                messages.error(request, 'This email is already registered. Please use a different email or sign in.')
                return render(request, 'users/register.html', {'form': form})
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username is already taken. Please choose a different one.')
                return render(request, 'users/register.html', {'form': form})
            
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
            
            from django.urls import reverse
            verification_url = request.build_absolute_uri(
                reverse('users:verify_email', args=[uid, token])
            )
            
            # Send verification email
            subject = 'Verify your email address - Ripple'
            html_message = render_to_string('users/email_verification.html', {
                'username': username,
                'verification_url': verification_url,
            })
            text_message = render_to_string('users/email_verification.txt', {
                'username': username,
                'verification_url': verification_url,
            })
            
            try:
                result = send_mail(
                    subject,
                    text_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email_value],
                    fail_silently=False,
                    html_message=html_message,
                )
                logger.info(f"Email sent successfully to {email_value}. send_mail returned: {result}")
                print(f"[Email] Successfully sent verification email to {email_value}")
            except Exception as e:
                # Log the error with full details
                error_msg = f"Failed to send email to {email_value}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"[Email] ERROR: {error_msg}")
                # Don't silently fail - show error to user if email is critical
                messages.error(request, 'Failed to send verification email. Please try again or contact support.')
                return render(request, 'users/register.html', {'form': form})
            
            return render(request, 'users/registration_success.html', {
                'email': email_value
            })
    else:
        form = UserCreationForm()
    # Add email field dynamically for a simple UX
    if not hasattr(form.fields, 'email'):
        form.fields['email'] = forms.EmailField(required=True, label='Email')
    return render(request, 'users/register.html', {'form': form})


def verify_email(request, uidb64, token):
    try:
        username = force_str(urlsafe_base64_decode(uidb64))
        user_data = request.session.get('user_data')
        
        if not user_data or user_data['username'] != username:
            return render(request, 'users/email_verification_failed.html')
            
        # Create the user only after email verification
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password']
        )
        
        # Clean up session data
        if 'user_data' in request.session:
            del request.session['user_data']
            
        return render(request, 'users/email_verification_success.html')
        
    except Exception as e:
        print(f"Error in email verification: {e}")
        return render(request, 'users/email_verification_failed.html')


def logout_direct(request):
    auth_logout(request)
    return redirect('core:landing')


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Custom password reset view with better error handling and logging"""
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    
    def get_users(self, email):
        """Override to add logging when users are found"""
        users = super().get_users(email)
        user_count = len(list(users)) if users else 0
        logger.info(f"[Password Reset] Found {user_count} user(s) for email: {email}")
        print(f"[Password Reset] Found {user_count} user(s) for email: {email}")
        
        # Convert to list to check, then return iterator
        user_list = list(users) if users else []
        if user_list:
            for user in user_list:
                logger.info(f"[Password Reset] User found: {user.username} (ID: {user.id}, active: {user.is_active})")
                print(f"[Password Reset] User found: {user.username} (ID: {user.id}, active: {user.is_active})")
        else:
            logger.warning(f"[Password Reset] No active users found for email: {email}")
            print(f"[Password Reset] WARNING: No active users found for email: {email}")
        
        # Return iterator
        return iter(user_list)
    
    def form_valid(self, form):
        """Override to handle email sending with better logging and explicit user checking"""
        email = form.cleaned_data.get('email', '').strip()
        logger.info(f"Password reset requested for email: {email}")
        print(f"[Password Reset] ========================================")
        print(f"[Password Reset] Request received for email: {email}")
        print(f"[Password Reset] ========================================")
        
        # Check email backend configuration
        from django.conf import settings
        logger.info(f"[Password Reset] Email backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        print(f"[Password Reset] Email backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        print(f"[Password Reset] From email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        
        # Manually check for users - Django's get_users uses email__iexact
        users = User.objects.filter(email__iexact=email, is_active=True)
        user_list = list(users)
        user_count = len(user_list)
        
        print(f"[Password Reset] Manually checking for users with email: {email}")
        print(f"[Password Reset] Found {user_count} active user(s)")
        
        if user_list:
            for user in user_list:
                logger.info(f"[Password Reset] User found: {user.username} (ID: {user.id}, email: {user.email})")
                print(f"[Password Reset] User found: {user.username} (ID: {user.id}, email: {user.email})")
            
            # Users exist - explicitly send email for each user
            print(f"[Password Reset] Users found - sending password reset emails...")
            
            # Get email context and send for each user
            from django.contrib.sites.shortcuts import get_current_site
            from django.template.loader import render_to_string
            from django.urls import reverse
            
            site = get_current_site(self.request)
            # Always use https in production, http only in local dev
            protocol = 'https' if (self.request.is_secure() or not settings.DEBUG) else 'http'
            print(f"[Password Reset] Using protocol: {protocol} (is_secure: {self.request.is_secure()}, DEBUG: {settings.DEBUG})")
            
            emails_sent = 0
            for user in user_list:
                try:
                    # Build context for email
                    context = {
                        'email': user.email,
                        'domain': site.domain,
                        'site_name': site.name,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'user': user,
                        'token': default_token_generator.make_token(user),
                        'protocol': protocol,
                    }
                    
                    # Get from_email
                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ripple.com')
                    
                    print(f"[Password Reset] Sending email to user: {user.username} ({user.email})")
                    
                    # Call our send_mail override
                    result = self.send_mail(
                        self.subject_template_name,
                        self.email_template_name,
                        context,
                        from_email,
                        user.email,
                        html_email_template_name=None,
                    )
                    
                    if result:
                        emails_sent += 1
                        logger.info(f"[Password Reset] Email sent successfully to {user.email}")
                        print(f"[Password Reset] Email sent successfully to {user.email}")
                    else:
                        logger.warning(f"[Password Reset] send_mail returned False for {user.email}")
                        print(f"[Password Reset] WARNING: send_mail returned False for {user.email}")
                        
                except Exception as e:
                    error_msg = f"Failed to send password reset email to {user.email}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    print(f"[Password Reset] ERROR: {error_msg}")
                    import traceback
                    print(f"[Password Reset] Traceback:\n{traceback.format_exc()}")
            
            if emails_sent > 0:
                logger.info(f"[Password Reset] Successfully sent {emails_sent} password reset email(s)")
                print(f"[Password Reset] Success! Sent {emails_sent} email(s)")
            else:
                logger.error(f"[Password Reset] Failed to send any emails")
                print(f"[Password Reset] ERROR: Failed to send any emails")
            
            # Always redirect to success (for security)
            return redirect(self.success_url)
        else:
            # No users found - but we still show success for security
            logger.warning(f"[Password Reset] No active users found for email: {email}")
            print(f"[Password Reset] WARNING: No active users found for email: {email}")
            print(f"[Password Reset] Checking all users with similar emails...")
            # Check if email exists at all (case insensitive)
            all_users = User.objects.filter(email__iexact=email)
            if all_users.exists():
                inactive_users = [u for u in all_users if not u.is_active]
                logger.warning(f"[Password Reset] Found {len(inactive_users)} inactive user(s) with this email")
                print(f"[Password Reset] Found {len(inactive_users)} inactive user(s) - email won't be sent")
            else:
                logger.warning(f"[Password Reset] No users found at all with email: {email}")
                print(f"[Password Reset] No users found at all with email: {email}")
            
            # Still redirect to success (security: don't reveal if email exists)
            return redirect(self.success_url)
    
    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        """Override send_mail to add better logging and error handling"""
        from django.template.loader import render_to_string
        from django.contrib.sites.shortcuts import get_current_site
        from django.conf import settings
        
        email = to_email
        logger.info(f"[Password Reset] send_mail called for: {email}")
        print(f"[Password Reset] ========================================")
        print(f"[Password Reset] send_mail METHOD CALLED!")
        print(f"[Password Reset] ========================================")
        print(f"[Password Reset] Recipient: {email}")
        print(f"[Password Reset] Subject template: {subject_template_name}")
        print(f"[Password Reset] Email template: {email_template_name}")
        print(f"[Password Reset] From email parameter: {from_email}")
        print(f"[Password Reset] Default from email setting: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        print(f"[Password Reset] Email backend: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        
        # Ensure from_email is set
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ripple.com')
            print(f"[Password Reset] Using default from_email: {from_email}")
        
        try:
            # Render subject and body
            subject = render_to_string(subject_template_name, context).strip()
            message = render_to_string(email_template_name, context)
            html_message = None
            if html_email_template_name:
                html_message = render_to_string(html_email_template_name, context)
            
            logger.info(f"[Password Reset] Email rendered - Subject: {subject[:50]}...")
            print(f"[Password Reset] Email rendered successfully")
            print(f"[Password Reset] Subject: {subject}")
            
            # Send the email using Django's send_mail
            from django.core.mail import send_mail
            result = send_mail(
                subject,
                message,
                from_email,
                [email],
                fail_silently=False,
                html_message=html_message,
            )
            
            logger.info(f"[Password Reset] Email sent via send_mail. Result: {result}")
            print(f"[Password Reset] Email sent successfully! Result: {result} (1=success, 0=failure)")
            return result
            
        except Exception as e:
            error_msg = f"Failed to send password reset email in send_mail: {str(e)}"
            logger.error(error_msg, exc_info=True)
            print(f"[Password Reset] ERROR in send_mail: {error_msg}")
            import traceback
            print(f"[Password Reset] Traceback:\n{traceback.format_exc()}")
            raise


# Profile Views
@login_required
def profile_view(request):
    """Display user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    evidence = profile.evidence.all()
    
    # Get latest identity submission for verification info
    latest_submission = profile.identity_submissions.order_by('-created_at').first()
    
    # Get user's skills
    teaching_skills = UserSkill.objects.filter(
        user=request.user, 
        can_teach=True
    ).select_related('skill')
    
    learning_skills = UserSkill.objects.filter(
        user=request.user, 
        wants_to_learn=True
    ).select_related('skill')
    
    # Get favorite classes
    from skills.models import ClassFavorite
    favorite_class_ids = ClassFavorite.objects.filter(user=request.user).values_list('teaching_class_id', flat=True)
    favorite_classes = TeachingClass.objects.filter(
        id__in=favorite_class_ids,
        is_published=True
    ).select_related('teacher').prefetch_related('topics').order_by('-created_at')
    
    context = {
        'profile': profile,
        'evidence': evidence,
        'latest_submission': latest_submission,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        # Classes authored by this user
        'my_classes_published': TeachingClass.objects.filter(teacher=request.user, is_published=True).order_by('-created_at'),
        'my_classes_drafts': TeachingClass.objects.filter(teacher=request.user, is_published=False).order_by('-created_at'),
        # Classes user is enrolled in as a student
        'enrolled_classes': ClassEnrollment.objects.filter(
            user=request.user,
            status=ClassEnrollment.ACTIVE
        ).select_related('teaching_class', 'teaching_class__teacher').order_by('-created_at'),
        # Pending teacher applications
        'my_pending_applications': TeacherApplication.objects.filter(applicant=request.user, status='pending').order_by('-created_at'),
        # Favorite classes
        'favorite_classes': favorite_classes,
    }
    return render(request, 'users/profile/profile.html', context)


def view_user_profile(request, username):
    """View another user's public profile"""
    from django.contrib.auth.models import User
    from django.db.models import Avg, Count, Q
    from skills.models import ClassReview, ClassEnrollment
    
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    
    # Get user's skills
    teaching_skills = UserSkill.objects.filter(
        user=user, 
        can_teach=True,
        verification_status='verified'  # Only show verified skills
    ).select_related('skill')
    
    learning_skills = UserSkill.objects.filter(
        user=user, 
        wants_to_learn=True
    ).select_related('skill')
    
    # Get public classes
    public_classes = TeachingClass.objects.filter(teacher=user, is_published=True).order_by('-created_at')
    
    # Calculate statistics
    total_classes = public_classes.count()
    total_students = ClassEnrollment.objects.filter(
        teaching_class__teacher=user,
        teaching_class__is_published=True,
        status=ClassEnrollment.ACTIVE
    ).count()
    
    # Get reviews for all classes
    reviews = ClassReview.objects.filter(teaching_class__teacher=user, teaching_class__is_published=True)
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Get recent reviews (last 3)
    recent_reviews = reviews.select_related('reviewer', 'teaching_class').order_by('-created_at')[:3]
    
    context = {
        'viewed_user': user,
        'profile': profile,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        'is_own_profile': request.user == user if request.user.is_authenticated else False,
        'public_classes': public_classes[:6],  # Show first 6 classes
        'total_classes': total_classes,
        'total_students': total_students,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'users/profile/view_profile.html', context)


@login_required
def profile_edit(request):
    """Edit user's profile with verification information"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        # Update user fields (first_name, last_name are stored on User model)
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()
        
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        
        # Create or update identity submission for verification data
        # Get the latest submission or create a new one
        latest_submission = profile.identity_submissions.order_by('-created_at').first()
        
        if latest_submission:
            # Update existing submission
            latest_submission.first_name = request.user.first_name
            latest_submission.last_name = request.user.last_name
            latest_submission.dob = request.POST.get('dob') or None
            latest_submission.nationality = request.POST.get('nationality', '')
            latest_submission.address1 = request.POST.get('address1', '')
            latest_submission.address2 = request.POST.get('address2', '')
            latest_submission.state = request.POST.get('state', '')
            latest_submission.postal = request.POST.get('postal', '')
            latest_submission.country = request.POST.get('country', '')
            latest_submission.save()
        else:
            # Create new submission
            IdentitySubmission.objects.create(
                profile=profile,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                dob=request.POST.get('dob') or None,
                nationality=request.POST.get('nationality', ''),
                address1=request.POST.get('address1', ''),
                address2=request.POST.get('address2', ''),
                state=request.POST.get('state', ''),
                postal=request.POST.get('postal', ''),
                country=request.POST.get('country', '')
            )
        
        messages.success(request, 'Profile updated successfully!')
        
        return redirect('users:profile')
    
    # Get latest identity submission for pre-filling form
    latest_submission = profile.identity_submissions.order_by('-created_at').first()
    
    context = {
        'profile': profile,
        'latest_submission': latest_submission,
    }
    return render(request, 'users/profile/profile_edit.html', context)


@login_required
def unverify_skill(request, skill_id):
    """Remove ability to teach a specific skill"""
    user_skill = get_object_or_404(UserSkill, user=request.user, skill_id=skill_id)
    user_skill.can_teach = False
    user_skill.save()
    
    messages.info(request, f'You are no longer teaching {user_skill.skill.name}.')
    return redirect('users:profile')


@login_required
def add_skill(request):
    """Add a new skill to user's profile"""
    if request.method == 'POST':
        skill_name = request.POST.get('skill_name', '').strip()
        level = request.POST.get('level', 'intermediate')
        skill_type = request.POST.get('skill_type', 'teach')  # 'teach' or 'learn'
        
        if skill_name:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            
            # Determine skill type based on form data
            can_teach = skill_type == 'teach'
            wants_to_learn = skill_type == 'learn'
            
            user_skill, created = UserSkill.objects.get_or_create(
                user=request.user,
                skill=skill,
                defaults={
                    'level': level,
                    'can_teach': can_teach,
                    'wants_to_learn': wants_to_learn
                }
            )
            
            if not created:
                # Update existing skill
                user_skill.level = level
                if skill_type == 'teach':
                    user_skill.can_teach = True
                elif skill_type == 'learn':
                    user_skill.wants_to_learn = True
                user_skill.save()
            
            messages.success(request, f'Added {skill.name} to your {skill_type}ing skills!')
        else:
            messages.error(request, 'Please enter a skill name.')
    
    return redirect('users:profile')


@login_required
def verify_skill(request, skill_id):
    """Show skill verification form"""
    skill = get_object_or_404(Skill, id=skill_id)
    user_skill = get_object_or_404(UserSkill, user=request.user, skill=skill)
    
    if not user_skill.can_teach:
        messages.error(request, 'You must be able to teach this skill to verify it.')
        return redirect('users:profile')
    
    evidence_list = user_skill.evidence.all()
    
    context = {
        'skill': skill,
        'user_skill': user_skill,
        'evidence_list': evidence_list,
    }
    return render(request, 'skills/verify_skill.html', context)


@login_required
def submit_evidence(request, skill_id):
    """Submit evidence for skill verification"""
    skill = get_object_or_404(Skill, id=skill_id)
    user_skill = get_object_or_404(UserSkill, user=request.user, skill=skill)
    
    if not user_skill.can_teach:
        messages.error(request, 'You must be able to teach this skill to verify it.')
        return redirect('users:profile')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        evidence_type = request.POST.get('evidence_type', 'document')
        description = request.POST.get('description', '').strip()
        link = request.POST.get('link', '').strip()
        is_primary = request.POST.get('is_primary') == 'on'
        
        if not title:
            messages.error(request, 'Please provide a title for your evidence.')
            return redirect('users:verify_skill', skill_id=skill_id)
        
        # Check if file or link is provided
        file = request.FILES.get('file')
        if not file and not link:
            messages.error(request, 'Please upload a file or provide a link.')
            return redirect('users:verify_skill', skill_id=skill_id)
        
        # Create evidence
        evidence = SkillEvidence.objects.create(
            user_skill=user_skill,
            title=title,
            evidence_type=evidence_type,
            file=file,
            link=link,
            description=description,
            is_primary=is_primary
        )
        
        # If this is the first evidence, mark skill as pending verification
        if user_skill.verification_status == UserSkill.UNVERIFIED:
            user_skill.verification_status = UserSkill.PENDING
            user_skill.save()
        
        messages.success(request, f'Evidence submitted for {skill.name}! Your skill is now pending verification.')
        return redirect('users:verify_skill', skill_id=skill_id)
    
    return redirect('users:verify_skill', skill_id=skill_id)


@login_required
def remove_evidence(request, evidence_id):
    """Remove evidence from skill verification"""
    evidence = get_object_or_404(SkillEvidence, id=evidence_id, user_skill__user=request.user)
    skill_id = evidence.user_skill.skill.id
    
    evidence.delete()
    messages.success(request, 'Evidence removed successfully.')
    return redirect('users:verify_skill', skill_id=skill_id)


@login_required
def delete_skill(request, skill_id):
    """Delete a skill from user's profile"""
    skill = get_object_or_404(Skill, id=skill_id)
    user_skill = get_object_or_404(UserSkill, user=request.user, skill=skill)
    user_skill.delete()
    messages.success(request, f'{skill.name} has been removed from your profile.')
    return redirect('users:profile')


@login_required
@require_http_methods(["GET", "POST"])
def verify_identity(request):
    """Simple identity verification intake: first/last name, DOB, address, country, and ID upload.
    Sets profile.verification_status to 'pending' when submitted.
    """
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        # Store minimal identity fields on the Django User/Profile
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()

        profile.location = request.POST.get('country', profile.location)
        # Mark as pending
        profile.verification_status = 'pending'
        profile.save()

        # Persist identity submission snapshot for admin review
        IdentitySubmission.objects.create(
            profile=profile,
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            dob=request.POST.get('dob') or None,
            nationality=request.POST.get('nationality',''),
            address1=request.POST.get('address1',''),
            address2=request.POST.get('address2',''),
            state=request.POST.get('state',''),
            postal=request.POST.get('postal',''),
            country=request.POST.get('country','')
        )

        uploaded_labels = []
        # Government ID
        if 'id_document' in request.FILES:
            Evidence.objects.create(
                profile=profile,
                title='Identity Document',
                file=request.FILES['id_document']
            )
            uploaded_labels.append('Government ID')
        # Selfie
        if 'selfie' in request.FILES:
            Evidence.objects.create(
                profile=profile,
                title='Selfie',
                file=request.FILES['selfie']
            )
            uploaded_labels.append('Selfie')
        # Proof of Address / Additional
        if 'address_doc' in request.FILES:
            Evidence.objects.create(
                profile=profile,
                title='Proof of Address',
                file=request.FILES['address_doc']
            )
            uploaded_labels.append('Proof of Address')

        if uploaded_labels:
            messages.success(request, 'Verification submitted with: ' + ', '.join(uploaded_labels) + '.')
        else:
            messages.success(request, 'Verification submitted. We will review your information shortly.')
        return redirect('users:profile')

    return render(request, 'users/profile/verify_identity.html', { 'profile': profile })


@staff_member_required
def admin_user_verifications(request):
    """List users with filter by verification status for admin review."""
    status = request.GET.get('status', 'pending')
    allowed = ['pending', 'verified', 'unverified', 'all']
    if status not in allowed:
        status = 'pending'
    qs = Profile.objects.select_related('user')
    if status != 'all':
        qs = qs.filter(verification_status=status)
    profiles = qs.order_by('user__username')
    # Build grouped evidence per profile for easier templating
    rows = []
    for p in profiles:
        docs = list(p.evidence.all())
        # mark image evidence for thumbnail rendering
        for d in docs:
            try:
                name = (d.file.name or '').lower()
            except Exception:
                name = ''
            d.is_image = name.endswith('.png') or name.endswith('.jpg') or name.endswith('.jpeg') or name.endswith('.webp') or name.endswith('.gif')
        latest_submission = p.identity_submissions.order_by('-created_at').first()
        rows.append({
            'profile': p,
            'id_docs': [e for e in docs if e.title == 'Identity Document'],
            'selfies': [e for e in docs if e.title == 'Selfie'],
            'proofs': [e for e in docs if e.title == 'Proof of Address'],
            'submission': latest_submission,
        })
    return render(request, 'users/profile/admin_user_verifications.html', { 'rows': rows, 'status': status })


@staff_member_required
def admin_user_verification_action(request, profile_id, action):
    """Approve or reject a user's identity verification."""
    profile = get_object_or_404(Profile, id=profile_id)
    
    try:
        if action == 'approve':
            profile.verification_status = 'verified'
            message = f"{profile.user.username} has been verified."
            message_type = 'success'
        elif action == 'reject':
            # Wipe identity evidence and submitted info on rejection
            evidence_count = 0
            for ev in list(profile.evidence.all()):
                try:
                    if ev.file:
                        ev.file.delete(save=False)
                    ev.delete()
                    evidence_count += 1
                except Exception:
                    pass
            profile.identity_submissions.all().delete()
            profile.verification_status = 'unverified'
            message = f"{profile.user.username}'s verification was rejected and {evidence_count} documents have been removed."
            message_type = 'info'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action'
            })
        
        profile.save()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'message_type': message_type,
                'action': action,
                'username': profile.user.username,
                'verification_status': profile.verification_status
            })
        else:
            if action == 'approve':
                messages.success(request, message)
            else:
                messages.info(request, message)
            return redirect('users:admin_user_verifications')
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error processing verification: {str(e)}'
            })
        else:
            messages.error(request, f'Error processing verification: {str(e)}')
            return redirect('users:admin_user_verifications')


@staff_member_required
def admin_user_skills(request):
    """List all users and their skills for admin management."""
    search_query = request.GET.get('search', '')
    skill_filter = request.GET.get('skill', '')
    
    # Get all users with their skills
    users = User.objects.select_related('profile').prefetch_related('user_skills__skill').all()
    
    if search_query:
        users = users.filter(username__icontains=search_query)
    
    # Build user data with skills
    user_data = []
    for user in users:
        teaching_skills = UserSkill.objects.filter(
            user=user, 
            can_teach=True
        ).select_related('skill')
        
        learning_skills = UserSkill.objects.filter(
            user=user, 
            wants_to_learn=True
        ).select_related('skill')
        
        if skill_filter:
            teaching_skills = teaching_skills.filter(skill__name__icontains=skill_filter)
            learning_skills = learning_skills.filter(skill__name__icontains=skill_filter)
        
        # Only include users who have skills or match search
        if teaching_skills.exists() or learning_skills.exists() or search_query:
            user_data.append({
                'user': user,
                'teaching_skills': teaching_skills,
                'learning_skills': learning_skills,
            })
    
    context = {
        'user_data': user_data,
        'search_query': search_query,
        'skill_filter': skill_filter,
    }
    return render(request, 'users/profile/admin_user_skills.html', context)


@staff_member_required
def admin_user_classes(request):
    """List all teaching classes grouped by teacher for admin management."""
    search_query = request.GET.get('search', '')
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', '')

    classes_qs = TeachingClass.objects.select_related('teacher', 'teacher__profile').prefetch_related('topics').order_by('teacher__username', 'title')

    if search_query:
        classes_qs = classes_qs.filter(teacher__username__icontains=search_query)

    if class_filter:
        classes_qs = classes_qs.filter(title__icontains=class_filter)

    if status_filter == 'published':
        classes_qs = classes_qs.filter(is_published=True)
    elif status_filter == 'unpublished':
        classes_qs = classes_qs.filter(is_published=False)

    classes_list = list(classes_qs)

    for teaching_class in classes_list:
        price_cents = teaching_class.price_cents or 0
        teaching_class.admin_price_display = f"${price_cents / 100:.2f}"

    teacher_map = {}
    for teaching_class in classes_list:
        teacher_id = teaching_class.teacher_id
        if teacher_id not in teacher_map:
            teacher_map[teacher_id] = {
                'teacher': teaching_class.teacher,
                'classes': [],
            }
        teacher_map[teacher_id]['classes'].append(teaching_class)

    teacher_data = []
    for data in teacher_map.values():
        classes = sorted(data['classes'], key=lambda cls: cls.created_at, reverse=True)
        teacher_data.append({
            'teacher': data['teacher'],
            'classes': classes,
            'published_count': sum(1 for cls in classes if cls.is_published),
            'unpublished_count': sum(1 for cls in classes if not cls.is_published),
        })

    teacher_data.sort(key=lambda entry: entry['teacher'].username.lower())

    context = {
        'teacher_data': teacher_data,
        'search_query': search_query,
        'class_filter': class_filter,
        'status_filter': status_filter,
        'total_classes': len(classes_list),
    }
    return render(request, 'users/profile/admin_user_classes.html', context)


@staff_member_required
def admin_delete_user_skill(request, user_id, skill_id):
    """Delete a specific skill from a user's profile."""
    try:
        user = get_object_or_404(User, id=user_id)
        user_skill = get_object_or_404(UserSkill, user=user, skill_id=skill_id)
        skill_name = user_skill.skill.name
        
        # Delete all related evidence first
        evidence_count = 0
        for evidence in user_skill.evidence.all():
            try:
                if evidence.file:
                    evidence.file.delete(save=False)
                evidence.delete()
                evidence_count += 1
            except Exception as e:
                print(f"Error deleting evidence: {e}")
        
        # Delete the user skill
        user_skill.delete()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Successfully removed skill "{skill_name}" from {user.username}\'s profile. Deleted {evidence_count} evidence items.'
            })
        else:
            messages.success(request, f'Successfully removed skill "{skill_name}" from {user.username}\'s profile. Deleted {evidence_count} evidence items.')
            return redirect('users:admin_user_skills')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting skill: {str(e)}'
            })
        else:
            messages.error(request, f'Error deleting skill: {str(e)}')
            return redirect('users:admin_user_skills')


@staff_member_required
def admin_delete_class(request, class_id):
    """Delete a specific teaching class."""
    try:
        teaching_class = get_object_or_404(TeachingClass, id=class_id)
        class_title = teaching_class.title
        teacher_username = teaching_class.teacher.username

        if teaching_class.thumbnail:
            teaching_class.thumbnail.delete(save=False)
        if teaching_class.intro_video:
            teaching_class.intro_video.delete(save=False)

        teaching_class.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted class "{class_title}" taught by {teacher_username}.'
            })
        else:
            messages.success(request, f'Successfully deleted class "{class_title}" taught by {teacher_username}.')
            return redirect('users:admin_user_classes')

    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting class: {str(e)}'
            })
        else:
            messages.error(request, f'Error deleting class: {str(e)}')
            return redirect('users:admin_user_classes')


@login_required
def view_verification_status(request):
    """View user's verification status and submitted documents"""
    profile = get_object_or_404(Profile, user=request.user)
    
    # Get all evidence submitted for verification
    evidence_list = profile.evidence.all()
    
    # Get latest identity submission
    latest_submission = profile.identity_submissions.order_by('-created_at').first()
    
    context = {
        'profile': profile,
        'evidence_list': evidence_list,
        'latest_submission': latest_submission,
    }
    return render(request, 'users/profile/verification_status.html', context)

@login_required
def applications_view(request):
    """Centralized view for all user applications and requests"""
    from skills.models import TeacherApplication
    
    # Get user's community requests
    community_requests = CommunityRequest.objects.filter(
        requester=request.user
    ).select_related('skill', 'reviewed_by').order_by('-created_at')
    
    # Get user's skill verifications (teaching applications)
    skill_verifications = UserSkill.objects.filter(
        user=request.user,
        can_teach=True
    ).select_related('skill').prefetch_related('evidence').order_by('-updated_at')
    
    # Get user's class applications (TeacherApplication)
    class_applications = TeacherApplication.objects.filter(
        applicant=request.user
    ).select_related('reviewer').order_by('-created_at')
    
    # Get user's identity verification status
    profile = request.user.profile
    identity_submissions = profile.identity_submissions.order_by('-created_at')
    latest_identity = identity_submissions.first()
    
    # Count statistics
    stats = {
        'total_applications': (
            community_requests.count() + 
            skill_verifications.count() + 
            class_applications.count() +
            (1 if latest_identity else 0)
        ),
        'pending_count': (
            community_requests.filter(status='pending').count() + 
            skill_verifications.filter(verification_status='pending').count() +
            class_applications.filter(status=TeacherApplication.PENDING).count() +
            (1 if profile.verification_status == 'pending' else 0)
        ),
        'approved_count': (
            community_requests.filter(status='approved').count() + 
            skill_verifications.filter(verification_status='verified').count() +
            class_applications.filter(status=TeacherApplication.APPROVED).count() +
            (1 if profile.verification_status == 'verified' else 0)
        ),
        'rejected_count': (
            community_requests.filter(status='rejected').count() + 
            skill_verifications.filter(verification_status='rejected').count() +
            class_applications.filter(status=TeacherApplication.REJECTED).count()
        ),
    }
    
    context = {
        'community_requests': community_requests,
        'skill_verifications': skill_verifications,
        'class_applications': class_applications,
        'profile': profile,
        'latest_identity': latest_identity,
        'identity_submissions': identity_submissions,
        'stats': stats,
    }
    
    return render(request, 'users/applications.html', context)
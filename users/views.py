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
from .models import Profile, Evidence, IdentitySubmission
from skills.models import UserSkill, Skill, SkillEvidence, TeachingClass, TeacherApplication
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from .message_utils import clear_all_messages
from communities.models import CommunityRequest
# Create your views here.

def custom_login(request):
    """Custom login view that clears irrelevant messages"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    # Clear all existing messages to prevent showing unrelated messages
    clear_all_messages(request)
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('core:home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    
    # Clear all existing messages to prevent showing unrelated messages
    clear_all_messages(request)
    
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
            
            send_mail(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [email_value],
                fail_silently=False,
                html_message=html_message,
            )
            
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
    
    context = {
        'profile': profile,
        'evidence': evidence,
        'latest_submission': latest_submission,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        # Classes authored by this user
        'my_classes_published': TeachingClass.objects.filter(teacher=request.user, is_published=True).order_by('-created_at'),
        'my_classes_drafts': TeachingClass.objects.filter(teacher=request.user, is_published=False).order_by('-created_at'),
        # Pending teacher applications
        'my_pending_applications': TeacherApplication.objects.filter(applicant=request.user, status='pending').order_by('-created_at'),
    }
    return render(request, 'users/profile/profile.html', context)


def view_user_profile(request, username):
    """View another user's public profile"""
    from django.contrib.auth.models import User
    
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
    
    context = {
        'viewed_user': user,
        'profile': profile,
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
        'is_own_profile': request.user == user if request.user.is_authenticated else False,
        'public_classes': TeachingClass.objects.filter(teacher=user, is_published=True).order_by('-created_at'),
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
from django.shortcuts import render, redirect, get_object_or_404
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
from .models import Profile, Evidence
from skills.models import UserSkill, Skill, SkillEvidence

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


# Profile Views
@login_required
def profile_view(request):
    """Display user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    evidence = profile.evidence.all()
    
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
        'teaching_skills': teaching_skills,
        'learning_skills': learning_skills,
    }
    return render(request, 'profile/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user's profile"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.location = request.POST.get('location', '')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'profile/profile_edit.html', context)


@login_required
def verify_skill(request, skill_id):
    """Verify ability to teach a specific skill"""
    skill = get_object_or_404(Skill, id=skill_id)
    user_skill, created = UserSkill.objects.get_or_create(
        user=request.user,
        skill=skill,
        defaults={'level': 'intermediate', 'can_teach': True}
    )
    
    if not created:
        user_skill.can_teach = True
        user_skill.save()
    
    messages.success(request, f'You can now teach {skill.name}!')
    return redirect('users:profile')


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
    return render(request, 'profile/verify_skill.html', context)


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



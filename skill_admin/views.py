from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from skills.models import UserSkill, Skill, SkillEvidence

# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def skill_review(request):
    """Admin view to review all pending skill verifications"""
    # Get all skills that are pending verification
    pending_skills = UserSkill.objects.filter(
        verification_status=UserSkill.PENDING,
        can_teach=True
    ).select_related('user', 'skill').prefetch_related('evidence')
    
    # Get skills by user for better organization
    users_with_pending_skills = {}
    for skill in pending_skills:
        user = skill.user
        if user not in users_with_pending_skills:
            users_with_pending_skills[user] = []
        users_with_pending_skills[user].append(skill)
    
    context = {
        'users_with_pending_skills': users_with_pending_skills,
        'total_pending': pending_skills.count(),
    }
    return render(request, 'admin/skill_review.html', context)

@user_passes_test(is_admin)
def skill_detail(request, user_id, skill_id):
    """Admin view to review specific skill evidence"""
    user = get_object_or_404(User, id=user_id)
    user_skill = get_object_or_404(UserSkill, user=user, skill_id=skill_id, can_teach=True)
    evidence_list = user_skill.evidence.all()
    
    context = {
        'user': user,
        'user_skill': user_skill,
        'evidence_list': evidence_list,
    }
    return render(request, 'admin/skill_detail.html', context)

@user_passes_test(is_admin)
def verify_skill(request, user_id, skill_id):
    """Admin action to verify a skill"""
    if request.method == 'POST':
        user_skill = get_object_or_404(UserSkill, user_id=user_id, skill_id=skill_id)
        verification_message = request.POST.get('verification_message', '').strip()
        
        user_skill.verification_status = UserSkill.VERIFIED
        user_skill.verification_message = verification_message
        user_skill.save()
        
        messages.success(request, f'Verified {user_skill.skill.name} for {user_skill.user.username}')
        return redirect('skill_admin:skill_review')
    
    return redirect('skill_admin:skill_detail', user_id=user_id, skill_id=skill_id)

@user_passes_test(is_admin)
def reject_skill(request, user_id, skill_id):
    """Admin action to reject a skill"""
    if request.method == 'POST':
        user_skill = get_object_or_404(UserSkill, user_id=user_id, skill_id=skill_id)
        verification_message = request.POST.get('verification_message', '').strip()
        
        user_skill.verification_status = UserSkill.REJECTED
        user_skill.verification_message = verification_message
        user_skill.save()
        
        messages.success(request, f'Rejected {user_skill.skill.name} for {user_skill.user.username}')
        return redirect('skill_admin:skill_review')
    
    return redirect('skill_admin:skill_detail', user_id=user_id, skill_id=skill_id)
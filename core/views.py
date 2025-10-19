from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from skills.models import Skill, UserSkill, Match
from communities.models import Community

def landing(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('core:home')
    return render(request, 'core/landing.html')

def home(request):
    user = request.user if request.user.is_authenticated else None

    # Featured skill: first skill or None
    featured_skill = Skill.objects.first()

    # User's communities if logged in; otherwise top 5 communities
    if user:
        user_communities = Community.objects.filter(members=user)[:5]
    else:
        user_communities = Community.objects.all()[:5]

    # Simple suggested matches: latest 6 matches
    recent_matches = Match.objects.all().order_by('-created_at')[:6]

    context = {
        'featured_skill': featured_skill,
        'user_communities': user_communities,
        'recent_matches': recent_matches,
    }
    return render(request, 'core/home.html', context)


def swipe(request):
    # Very simple prototype: show one random skill card
    skill = Skill.objects.order_by('?').first()
    context = {
        'card_skill': skill,
    }
    return render(request, 'core/swipe.html', context)


def search(request):
    from django.contrib.auth.models import User
    from django.db.models import Q, Count
    
    q = request.GET.get('q', '').strip()
    
    # Search users
    user_results = []
    if q:
        user_results = User.objects.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        ).exclude(is_superuser=True).select_related('profile')[:10]
    
    # Search skills with teacher counts
    skill_results = []
    if q:
        skill_results = Skill.objects.filter(name__icontains=q).annotate(
            teachers_count=Count('userskill', filter=Q(userskill__can_teach=True))
        )[:10]
    
    # Search communities
    community_results = Community.objects.filter(name__icontains=q)[:10] if q else []
    
    return render(request, 'core/search.html', {
        'q': q,
        'user_results': user_results,
        'skill_results': skill_results,
        'community_results': community_results,
    })


def skill_detail(request, skill_id):
    """Show all users who teach a specific skill"""
    from django.contrib.auth.models import User
    
    skill = get_object_or_404(Skill, id=skill_id)
    
    # Get all users who can teach this skill
    teachers = UserSkill.objects.filter(
        skill=skill,
        can_teach=True,
        verification_status='verified'
    ).select_related('user', 'user__profile').order_by('-level')
    
    # Get all users learning this skill
    learners = UserSkill.objects.filter(
        skill=skill,
        wants_to_learn=True
    ).select_related('user', 'user__profile')[:10]
    
    context = {
        'skill': skill,
        'teachers': teachers,
        'learners': learners,
        'teachers_count': teachers.count(),
        'learners_count': learners.count(),
    }
    return render(request, 'core/skill_detail.html', context)
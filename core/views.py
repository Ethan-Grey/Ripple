from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from skills.models import Skill, UserSkill, Match
from communities.models import Community
from django.http import JsonResponse
from skills.models import Skill, SwipeAction
from django.views.decorators.http import require_http_methods
import json

def landing(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('core:home')
    return render(request, 'core/landing.html')

def home(request):
    user = request.user if request.user.is_authenticated else None

    # Featured skills of the day: Get 5 quality skills with descriptions
    featured_skills = Skill.objects.filter(
        description__isnull=False
    ).exclude(
        description=''
    ).order_by('?')[:5]
    
    # If we don't have 5 skills with descriptions, just get any 5
    if featured_skills.count() < 5:
        featured_skills = Skill.objects.order_by('?')[:5]

    # User's communities if logged in
    user_communities = []
    if user:
        user_communities = Community.objects.filter(members=user)[:5]

    # Recent matches - only show matches involving the logged-in user
    recent_matches = []
    if user:
        recent_matches = Match.objects.filter(
            Q(user_a=user) | Q(user_b=user)
        ).select_related('user_a', 'user_b').order_by('-created_at')[:2]

    # Matched users - users who share complementary skills with current user
    matched_users = []
    if user:
        # Get skills the user wants to learn
        user_learning_skills = UserSkill.objects.filter(
            user=user, 
            wants_to_learn=True
        ).values_list('skill_id', flat=True)
        
        # Find users who can teach those skills
        if user_learning_skills:
            potential_matches = UserSkill.objects.filter(
                skill_id__in=user_learning_skills,
                can_teach=True
            ).exclude(user=user).select_related('user', 'skill')[:6]
            
            # Get unique users with their teaching skill
            seen_users = set()
            for us in potential_matches:
                if us.user.id not in seen_users:
                    matched_users.append({
                        'user': us.user,
                        'skill': us.skill
                    })
                    seen_users.add(us.user.id)

    context = {
        'featured_skills': featured_skills,
        'user_communities': user_communities,
        'recent_matches': recent_matches,
        'matched_users': matched_users,
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

@login_required
def swipe(request):
    """Swipe interface for discovering skills"""
    # Get skills user hasn't swiped on yet
    swiped_skill_ids = SwipeAction.objects.filter(
        user=request.user
    ).values_list('skill_id', flat=True)
    
    # Get next skill to show
    available_skills = Skill.objects.exclude(
        id__in=swiped_skill_ids
    ).order_by('?')
    
    card_skill = available_skills.first()
    
    # Get whitelist and blacklist counts
    whitelist_count = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_RIGHT
    ).count()
    
    blacklist_count = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_LEFT
    ).count()
    
    context = {
        'card_skill': card_skill,
        'whitelist_count': whitelist_count,
        'blacklist_count': blacklist_count,
        'total_skills': Skill.objects.count(),
        'swiped_count': len(swiped_skill_ids),
    }
    return render(request, 'core/swipe.html', context)


@login_required
@require_http_methods(["POST"])
def swipe_action(request):
    """Handle swipe left/right actions via AJAX"""
    try:
        data = json.loads(request.body)
        skill_id = data.get('skill_id')
        action = data.get('action')  # 'left' or 'right'
        
        if not skill_id or action not in ['left', 'right']:
            return JsonResponse({'error': 'Invalid data'}, status=400)
        
        skill = get_object_or_404(Skill, id=skill_id)
        
        # Create or update swipe action
        swipe, created = SwipeAction.objects.update_or_create(
            user=request.user,
            skill=skill,
            defaults={'action': action}
        )
        
        # Get next skill
        swiped_skill_ids = SwipeAction.objects.filter(
            user=request.user
        ).values_list('skill_id', flat=True)
        
        next_skill = Skill.objects.exclude(
            id__in=swiped_skill_ids
        ).order_by('?').first()
        
        # Get updated counts
        whitelist_count = SwipeAction.objects.filter(
            user=request.user,
            action=SwipeAction.SWIPE_RIGHT
        ).count()
        
        blacklist_count = SwipeAction.objects.filter(
            user=request.user,
            action=SwipeAction.SWIPE_LEFT
        ).count()
        
        response_data = {
            'success': True,
            'action': action,
            'whitelist_count': whitelist_count,
            'blacklist_count': blacklist_count,
        }
        
        if next_skill:
            response_data['next_skill'] = {
                'id': next_skill.id,
                'name': next_skill.name,
                'description': next_skill.description or 'No description available'
            }
        else:
            response_data['no_more_skills'] = True
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def view_whitelist(request):
    """View whitelisted skills"""
    whitelist = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_RIGHT
    ).select_related('skill')
    
    return render(request, 'core/whitelist.html', {'whitelist': whitelist})


@login_required
def view_blacklist(request):
    """View blacklisted skills"""
    blacklist = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_LEFT
    ).select_related('skill')
    
    return render(request, 'core/blacklist.html', {'blacklist': blacklist})


@login_required
@require_http_methods(["POST"])
def remove_swipe_action(request, skill_id):
    """Remove a swipe action (undo swipe)"""
    try:
        SwipeAction.objects.filter(
            user=request.user,
            skill_id=skill_id
        ).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from skills.models import Skill, UserSkill, Match, TeachingClass, SwipeAction
from communities.models import Community
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

def landing(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('core:home')
    return render(request, 'core/landing.html')

def about(request):
    """About Us page"""
    return render(request, 'core/about.html')

def contact(request):
    """Contact Us page"""
    return render(request, 'core/contact.html')
    
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
    """Swipe interface for discovering classes"""
    # Get classes user hasn't swiped on yet (only published classes)
    swiped_class_ids = SwipeAction.objects.filter(
        user=request.user
    ).values_list('teaching_class_id', flat=True)
    
    # Get next class to show (only published classes)
    available_classes = TeachingClass.objects.filter(
        is_published=True
    ).exclude(
        id__in=swiped_class_ids
    ).select_related('teacher').prefetch_related('topics').order_by('?')
    
    card_class = available_classes.first()
    
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
        'card_class': card_class,
        'whitelist_count': whitelist_count,
        'blacklist_count': blacklist_count,
        'total_classes': TeachingClass.objects.filter(is_published=True).count(),
        'swiped_count': len(swiped_class_ids),
        'has_swiped': len(swiped_class_ids) > 0,  # Show stats only if user has swiped
    }
    return render(request, 'core/swipe.html', context)


@login_required
@require_http_methods(["POST"])
def swipe_action(request):
    """Handle swipe left/right actions via AJAX"""
    try:
        data = json.loads(request.body)
        class_id = data.get('class_id')
        action = data.get('action')  # 'left' or 'right'
        
        if not class_id or action not in ['left', 'right']:
            return JsonResponse({'error': 'Invalid data'}, status=400)
        
        teaching_class = get_object_or_404(TeachingClass, id=class_id, is_published=True)
        
        # Create or update swipe action
        swipe, created = SwipeAction.objects.update_or_create(
            user=request.user,
            teaching_class=teaching_class,
            defaults={'action': action}
        )
        
        # Get next class
        swiped_class_ids = SwipeAction.objects.filter(
            user=request.user
        ).values_list('teaching_class_id', flat=True)
        
        next_class = TeachingClass.objects.filter(
            is_published=True
        ).exclude(
            id__in=swiped_class_ids
        ).select_related('teacher').prefetch_related('topics').order_by('?').first()
        
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
        
        if next_class:
            response_data['next_class'] = {
                'id': next_class.id,
                'title': next_class.title,
                'short_description': next_class.short_description or 'No description available',
                'teacher': next_class.teacher.username,
                'difficulty': next_class.get_difficulty_display(),
                'duration_minutes': next_class.duration_minutes,
                'price_cents': next_class.price_cents,
                'topics': [topic.name for topic in next_class.topics.all()[:3]],
                'slug': next_class.slug,
            }
        else:
            response_data['no_more_classes'] = True
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def view_whitelist(request):
    """View whitelisted classes"""
    whitelist = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_RIGHT
    ).select_related('teaching_class', 'teaching_class__teacher').prefetch_related('teaching_class__topics')
    
    # Get enrolled class IDs for badges
    from skills.models import ClassEnrollment
    enrolled_class_ids = ClassEnrollment.objects.filter(
        user=request.user,
        status=ClassEnrollment.ACTIVE
    ).values_list('teaching_class_id', flat=True)
    
    return render(request, 'core/whitelist.html', {
        'whitelist': whitelist,
        'enrolled_class_ids': enrolled_class_ids
    })

@login_required
def view_blacklist(request):
    """View blacklisted classes"""
    blacklist = SwipeAction.objects.filter(
        user=request.user,
        action=SwipeAction.SWIPE_LEFT
    ).select_related('teaching_class', 'teaching_class__teacher').prefetch_related('teaching_class__topics')
    
    return render(request, 'core/blacklist.html', {'blacklist': blacklist})


@login_required
@require_http_methods(["POST"])
def remove_swipe_action(request, class_id):
    """Remove a swipe action (undo swipe)"""
    try:
        SwipeAction.objects.filter(
            user=request.user,
            teaching_class_id=class_id
        ).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
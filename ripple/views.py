from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from skills.models import Skill, UserSkill, Match
from communities.models import Community
from django.shortcuts import render, redirect

def landing(request):
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'landing.html')

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
    return render(request, 'home.html', context)


def swipe(request):
    # Very simple prototype: show one random skill card
    skill = Skill.objects.order_by('?').first()
    context = {
        'card_skill': skill,
    }
    return render(request, 'swipe.html', context)


def communities_page(request):
    communities = Community.objects.select_related('skill').all().order_by('name')
    return render(request, 'communities.html', {'communities': communities})


def messages_page(request):
    return render(request, 'messages.html')




def search(request):
    q = request.GET.get('q', '').strip()
    skill_results = Skill.objects.filter(name__icontains=q)[:10] if q else []
    community_results = Community.objects.filter(name__icontains=q)[:10] if q else []
    return render(request, 'search.html', {
        'q': q,
        'skill_results': skill_results,
        'community_results': community_results,
    })


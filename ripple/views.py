from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from skills.models import Skill, UserSkill, Match
from communities.models import Community
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User

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


def profile_page(request):
    return render(request, 'profile.html')


def search(request):
    q = request.GET.get('q', '').strip()
    skill_results = Skill.objects.filter(name__icontains=q)[:10] if q else []
    community_results = Community.objects.filter(name__icontains=q)[:10] if q else []
    return render(request, 'search.html', {
        'q': q,
        'skill_results': skill_results,
        'community_results': community_results,
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user: User = form.save()
            # Save email if provided
            email_value = request.POST.get('email')
            if email_value:
                user.email = email_value
                user.save(update_fields=['email'])
            # Auto-login after registration
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    # Add email field dynamically for a simple UX
    if not hasattr(form.fields, 'email'):
        from django import forms
        form.fields['email'] = forms.EmailField(required=False)
    return render(request, 'auth/register.html', {'form': form})


def logout_direct(request):
    auth_logout(request)
    return redirect('login')
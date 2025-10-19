from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Community, CommunityRequest, Post, Comment
from skills.models import Skill


def communities_page(request):
    """List all approved communities with filtering"""
    skill_filter = request.GET.get('skill', 'all')
    
    communities = Community.objects.filter(is_approved=True).select_related('skill', 'creator').prefetch_related('members').annotate(
        member_count_annotated=Count('members')
    )
    
    # Apply skill filter
    if skill_filter != 'all':
        communities = communities.filter(skill__id=skill_filter)
    
    communities = communities.all()
    
    # Get all skills for filter dropdown
    skills = Skill.objects.all().order_by('name')
    
    return render(request, 'communities/communities.html', {
        'communities': communities,
        'skills': skills,
        'current_skill_filter': skill_filter,
    })


def community_detail(request, pk):
    """View community with posts"""
    community = get_object_or_404(
        Community.objects.select_related('skill', 'creator').prefetch_related('members'),
        pk=pk,
        is_approved=True
    )
    
    # Get posts with vote counts
    posts = community.posts.select_related('author', 'author__profile').prefetch_related('upvotes', 'downvotes').annotate(
        comment_count_annotated=Count('comments')
    ).all()
    
    # Check if user is a member
    is_member = request.user.is_authenticated and request.user in community.members.all()
    
    return render(request, 'communities/community_detail.html', {
        'community': community,
        'posts': posts,
        'is_member': is_member,
    })


@login_required
def join_community(request, pk):
    """Join a community"""
    community = get_object_or_404(Community, pk=pk, is_approved=True)
    
    if request.user not in community.members.all():
        community.members.add(request.user)
        messages.success(request, f"You've joined {community.name}!")
    
    return redirect('communities:community_detail', pk=pk)


@login_required
def leave_community(request, pk):
    """Leave a community"""
    community = get_object_or_404(Community, pk=pk)
    
    if request.user in community.members.all():
        community.members.remove(request.user)
        messages.success(request, f"You've left {community.name}")
    
    return redirect('communities:community_detail', pk=pk)


@login_required
def create_post(request, community_pk):
    """Create a new post in a community"""
    community = get_object_or_404(Community, pk=community_pk, is_approved=True)
    
    # Check if user is a member
    if request.user not in community.members.all():
        messages.error(request, "You must be a member to post in this community.")
        return redirect('communities:community_detail', pk=community_pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        link = request.POST.get('link', '')
        image = request.FILES.get('image')
        
        if title and content:
            post = Post.objects.create(
                community=community,
                author=request.user,
                title=title,
                content=content,
                link=link,
                image=image
            )
            messages.success(request, "Post created successfully!")
            return redirect('communities:post_detail', community_pk=community_pk, post_pk=post.pk)
        else:
            messages.error(request, "Title and content are required.")
    
    return render(request, 'communities/create_post.html', {'community': community})


def post_detail(request, community_pk, post_pk):
    """View a post with comments"""
    post = get_object_or_404(
        Post.objects.select_related('community', 'author', 'author__profile'),
        pk=post_pk,
        community__pk=community_pk,
        community__is_approved=True
    )
    
    # Get top-level comments (no parent) with their replies
    comments = post.comments.filter(parent=None).select_related('author', 'author__profile').prefetch_related(
        'replies__author', 'replies__author__profile', 'upvotes', 'downvotes'
    ).all()
    
    # Check if user is a member
    is_member = request.user.is_authenticated and request.user in post.community.members.all()
    
    # Check user's vote on post
    user_vote = None
    if request.user.is_authenticated:
        if request.user in post.upvotes.all():
            user_vote = 'up'
        elif request.user in post.downvotes.all():
            user_vote = 'down'
    
    return render(request, 'communities/post_detail.html', {
        'post': post,
        'community': post.community,
        'comments': comments,
        'is_member': is_member,
        'user_vote': user_vote,
    })


@login_required
def add_comment(request, community_pk, post_pk):
    """Add a comment to a post"""
    post = get_object_or_404(Post, pk=post_pk, community__pk=community_pk)
    
    # Check if user is a member
    if request.user not in post.community.members.all():
        messages.error(request, "You must be a member to comment.")
        return redirect('communities:post_detail', community_pk=community_pk, post_pk=post_pk)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if content:
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, pk=parent_id)
            
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
                parent=parent
            )
            messages.success(request, "Comment added!")
        else:
            messages.error(request, "Comment cannot be empty.")
    
    return redirect('communities:post_detail', community_pk=community_pk, post_pk=post_pk)


@login_required
def vote_post(request, community_pk, post_pk):
    """Vote on a post (AJAX)"""
    post = get_object_or_404(Post, pk=post_pk, community__pk=community_pk)
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    # Check if user is a member
    if request.user not in post.community.members.all():
        return JsonResponse({'error': 'You must be a member to vote'}, status=403)
    
    # Check current vote status
    has_upvoted = request.user in post.upvotes.all()
    has_downvoted = request.user in post.downvotes.all()
    
    # Remove existing votes
    post.upvotes.remove(request.user)
    post.downvotes.remove(request.user)
    
    # Toggle logic: if clicking same vote, just remove it (already removed above)
    # If clicking different vote, add new vote
    if vote_type == 'up' and not has_upvoted:
        post.upvotes.add(request.user)
        user_vote = 'up'
    elif vote_type == 'down' and not has_downvoted:
        post.downvotes.add(request.user)
        user_vote = 'down'
    else:
        user_vote = None  # Removed vote (toggle off)
    
    return JsonResponse({
        'score': post.score,
        'user_vote': user_vote
    })


@login_required
def vote_comment(request, comment_pk):
    """Vote on a comment (AJAX)"""
    comment = get_object_or_404(Comment, pk=comment_pk)
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    # Check if user is a member
    if request.user not in comment.post.community.members.all():
        return JsonResponse({'error': 'You must be a member to vote'}, status=403)
    
    # Check current vote status
    has_upvoted = request.user in comment.upvotes.all()
    has_downvoted = request.user in comment.downvotes.all()
    
    # Remove existing votes
    comment.upvotes.remove(request.user)
    comment.downvotes.remove(request.user)
    
    # Toggle logic: if clicking same vote, just remove it (already removed above)
    # If clicking different vote, add new vote
    if vote_type == 'up' and not has_upvoted:
        comment.upvotes.add(request.user)
        user_vote = 'up'
    elif vote_type == 'down' and not has_downvoted:
        comment.downvotes.add(request.user)
        user_vote = 'down'
    else:
        user_vote = None  # Removed vote (toggle off)
    
    return JsonResponse({
        'score': comment.score,
        'user_vote': user_vote
    })


@login_required
def request_community(request):
    """Request to create a new community"""
    if request.method == 'POST':
        name = request.POST.get('name')
        skill_id = request.POST.get('skill')
        description = request.POST.get('description')
        reason = request.POST.get('reason')
        
        if name and skill_id and description and reason:
            skill = get_object_or_404(Skill, pk=skill_id)
            
            CommunityRequest.objects.create(
                requester=request.user,
                name=name,
                skill=skill,
                description=description,
                reason=reason
            )
            
            messages.success(request, "Your community request has been submitted! Admins will review it soon.")
            return redirect('communities:communities')
        else:
            messages.error(request, "All fields are required.")
    
    skills = Skill.objects.all().order_by('name')
    return render(request, 'communities/request_community.html', {'skills': skills})


@login_required
def my_community_requests(request):
    """View user's community requests"""
    requests_list = CommunityRequest.objects.filter(requester=request.user).select_related('skill', 'reviewed_by')
    return render(request, 'communities/my_requests.html', {'requests': requests_list})


@login_required
def delete_post(request, community_pk, post_pk):
    """Delete a post (author only)"""
    post = get_object_or_404(Post, pk=post_pk, community__pk=community_pk)
    
    # Check if user is the author
    if request.user != post.author:
        messages.error(request, "You can only delete your own posts.")
        return redirect('communities:post_detail', community_pk=community_pk, post_pk=post_pk)
    
    if request.method == 'POST':
        community_pk = post.community.pk
        post.delete()
        messages.success(request, "Your post has been deleted.")
        return redirect('communities:community_detail', pk=community_pk)
    
    return render(request, 'communities/confirm_delete_post.html', {'post': post})
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from .models import Community, CommunityRequest, Post, Comment
from skills.models import Skill


def communities_page(request):
    """List all approved communities with filtering"""
    skill_param = request.GET.get('skill', '')
    filter_type = request.GET.get('filter', 'all')  # 'all' or 'my'
    
    # Handle comma-separated skill IDs
    selected_skills = []
    if skill_param and skill_param != 'all':
        # Split by comma and filter out empty strings
        selected_skills = [s.strip() for s in skill_param.split(',') if s.strip()]
    
    # Get approved communities
    communities = Community.objects.filter(
        is_approved=True
    ).select_related(
        'skill', 'creator'
    ).prefetch_related(
        'members'
    )
    
    # Apply skill filter - handle multiple skills
    if selected_skills:
        communities = communities.filter(skill__id__in=selected_skills)
    
    # Apply "My Communities" filter
    if filter_type == 'my' and request.user.is_authenticated:
        communities = communities.filter(members=request.user)
    
    # Order by newest first
    communities = communities.order_by('-created_at')
    
    # Get all skills for filter dropdown
    skills = Skill.objects.all().order_by('name')
    
    return render(request, 'communities/communities.html', {
        'communities': communities,
        'skills': skills,
        'selected_skills': selected_skills,
        'filter_type': filter_type,
    })


def community_detail(request, pk):
    """View community with posts"""
    community = get_object_or_404(
        Community.objects.select_related('skill', 'creator').prefetch_related('members'),
        pk=pk,
        is_approved=True
    )
    
    # Get posts with comments count
    posts = community.posts.select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'upvotes', 'downvotes'
    ).annotate(
        comment_count_annotated=Count('comments')
    ).order_by('-is_pinned', '-created_at')
    
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
    else:
        messages.info(request, f"You're already a member of {community.name}")
    
    return redirect('communities:community_detail', pk=pk)


@login_required
def leave_community(request, pk):
    """Leave a community"""
    community = get_object_or_404(Community, pk=pk)
    
    if request.user in community.members.all():
        community.members.remove(request.user)
        messages.success(request, f"You've left {community.name}")
    else:
        messages.info(request, "You're not a member of this community")
    
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
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        link = request.POST.get('link', '').strip()
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
    comments = post.comments.filter(
        parent=None
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'replies__author', 
        'replies__author__profile', 
        'upvotes', 
        'downvotes'
    ).order_by('-created_at')
    
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
        content = request.POST.get('content', '').strip()
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
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    post = get_object_or_404(Post, pk=post_pk, community__pk=community_pk)
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    # Check if user is a member
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'You must be logged in to vote'}, status=403)
    
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
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=400)
    
    comment = get_object_or_404(Comment, pk=comment_pk)
    vote_type = request.POST.get('vote_type')  # 'up' or 'down'
    
    # Check if user is a member
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'You must be logged in to vote'}, status=403)
    
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
        name = request.POST.get('name', '').strip()
        skill_id = request.POST.get('skill')
        description = request.POST.get('description', '').strip()
        reason = request.POST.get('reason', '').strip()
        
        if name and skill_id and description and reason:
            skill = get_object_or_404(Skill, pk=skill_id)
            
            # Check if community with this name already exists
            if Community.objects.filter(name__iexact=name).exists():
                messages.error(request, "A community with this name already exists.")
                skills = Skill.objects.all().order_by('name')
                return render(request, 'communities/request_community.html', {
                    'skills': skills,
                    'name': name,
                    'description': description,
                    'reason': reason
                })
            
            # Check if user already has a pending request for this name
            if CommunityRequest.objects.filter(
                requester=request.user, 
                name__iexact=name, 
                status='pending'
            ).exists():
                messages.warning(request, "You already have a pending request for a community with this name.")
                return redirect('communities:my_requests')
            
            CommunityRequest.objects.create(
                requester=request.user,
                name=name,
                skill=skill,
                description=description,
                reason=reason
            )
            
            messages.success(request, "Your community request has been submitted! Admins will review it soon.")
            return redirect('communities:my_requests')
        else:
            messages.error(request, "All fields are required.")
    
    skills = Skill.objects.all().order_by('name')
    return render(request, 'communities/request_community.html', {'skills': skills})


@login_required
def my_community_requests(request):
    """View user's community requests"""
    requests_list = CommunityRequest.objects.filter(
        requester=request.user
    ).select_related(
        'skill', 'reviewed_by'
    ).order_by('-created_at')
    
    return render(request, 'communities/my_requests.html', {'requests': requests_list})


@login_required
def delete_post(request, community_pk, post_pk):
    """Delete a post (author or staff only)"""
    post = get_object_or_404(Post, pk=post_pk, community__pk=community_pk)
    
    # Check if user is the author or a staff member
    if request.user != post.author and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('communities:post_detail', community_pk=community_pk, post_pk=post_pk)
    
    if request.method == 'POST':
        community_pk = post.community.pk
        post_title = post.title
        post.delete()
        messages.success(request, f'Post "{post_title}" has been deleted.')
        return redirect('communities:community_detail', pk=community_pk)
    
    return render(request, 'communities/confirm_delete_post.html', {
        'post': post,
        'community': post.community
    })


@staff_member_required
def admin_community_requests(request):
    """Admin view to review community requests"""
    status_filter = request.GET.get('status', 'pending')
    allowed_statuses = ['all', 'pending', 'approved', 'rejected']
    
    if status_filter not in allowed_statuses:
        status_filter = 'pending'
    
    # Get requests based on status filter
    requests_query = CommunityRequest.objects.select_related(
        'requester', 'skill', 'reviewed_by'
    )
    
    if status_filter != 'all':
        requests_query = requests_query.filter(status=status_filter)
    
    requests_list = requests_query.order_by('-created_at')
    
    return render(request, 'communities/admin_community_requests.html', {
        'requests': requests_list,
        'status_filter': status_filter,
    })


@staff_member_required
def admin_community_request_action(request, request_id, action):
    """Approve or reject a community request"""
    community_request = get_object_or_404(CommunityRequest, pk=request_id)
    
    if action == 'approve':
        # Create the community
        community = Community.objects.create(
            name=community_request.name,
            skill=community_request.skill,
            description=community_request.description,
            creator=community_request.requester,
            is_approved=True
        )
        # Add the creator as a member
        community.members.add(community_request.requester)
        
        # Update request status
        community_request.status = CommunityRequest.APPROVED
        community_request.reviewed_by = request.user
        community_request.reviewed_at = timezone.now()
        community_request.save()
        
        messages.success(request, f'Community "{community_request.name}" has been approved and created!')
        
    elif action == 'reject':
        # Update request status
        community_request.status = CommunityRequest.REJECTED
        community_request.reviewed_by = request.user
        community_request.reviewed_at = timezone.now()
        community_request.save()
        
        messages.info(request, f'Community request "{community_request.name}" has been rejected.')
    
    return redirect('communities:admin_community_requests')


@staff_member_required
def delete_community(request, pk):
    """Delete a community (admin only)"""
    community = get_object_or_404(Community, pk=pk)
    
    if request.method == 'POST':
        community_name = community.name
        community.delete()
        messages.success(request, f'Community "{community_name}" has been deleted.')
        return redirect('communities:communities')
    
    return render(request, 'communities/confirm_delete_community.html', {
        'community': community
    })
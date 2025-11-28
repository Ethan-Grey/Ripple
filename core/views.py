from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from skills.models import Skill, UserSkill, Match, TeachingClass, SwipeAction, ClassEnrollment, ClassBooking, ClassTimeSlot, TeacherApplication, ClassReview
from communities.models import Community, CommunityRequest, Post, Comment
from chat.models import Conversation, Message, MessageStatus
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.contrib.contenttypes.models import ContentType
from core.models import Report, UserWarning
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import timedelta
from users.models import Profile, Evidence, IdentitySubmission


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

    # Dashboard stats and data (only for logged-in users)
    dashboard_stats = {}
    upcoming_sessions = []
    recommended_classes = []
    recent_conversations = []
    teaching_stats = {}
    pending_applications_count = 0
    
    if user:
        # Quick Stats
        dashboard_stats = {
            'classes_enrolled': ClassEnrollment.objects.filter(
                user=user, 
                status=ClassEnrollment.ACTIVE
            ).count(),
            'upcoming_sessions_count': ClassBooking.objects.filter(
                student=user,
                status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING],
                time_slot__start_time__gte=timezone.now()
            ).count(),
            'unread_messages': MessageStatus.objects.filter(
                user=user,
                is_read=False
            ).exclude(
                message__sender=user
            ).count(),
        }
        
        # Pending applications count
        from users.models import Profile
        try:
            profile = user.profile
            identity_pending = 1 if profile.verification_status == 'pending' else 0
        except:
            identity_pending = 0
        
        skill_pending = UserSkill.objects.filter(
            user=user,
            verification_status='pending'
        ).count()
        
        community_pending = CommunityRequest.objects.filter(
            requester=user,
            status='pending'
        ).count()
        
        class_pending = TeacherApplication.objects.filter(
            applicant=user,
            status='pending'
        ).count()
        
        pending_applications_count = identity_pending + skill_pending + community_pending + class_pending
        dashboard_stats['pending_applications'] = pending_applications_count
        
        # Upcoming Class Sessions (next 7 days)
        seven_days_from_now = timezone.now() + timedelta(days=7)
        upcoming_sessions = ClassBooking.objects.filter(
            student=user,
            status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING],
            time_slot__start_time__gte=timezone.now(),
            time_slot__start_time__lte=seven_days_from_now
        ).select_related(
            'time_slot', 
            'time_slot__teaching_class',
            'time_slot__teaching_class__teacher'
        ).order_by('time_slot__start_time')[:5]
        
        # Recommended Classes (from whitelist that user hasn't enrolled in)
        whitelisted_class_ids = SwipeAction.objects.filter(
            user=user,
            action=SwipeAction.SWIPE_RIGHT
        ).values_list('teaching_class_id', flat=True)
        
        enrolled_class_ids = ClassEnrollment.objects.filter(
            user=user,
            status=ClassEnrollment.ACTIVE
        ).values_list('teaching_class_id', flat=True)
        
        recommended_class_ids = set(whitelisted_class_ids) - set(enrolled_class_ids)
        recommended_classes = TeachingClass.objects.filter(
            id__in=recommended_class_ids,
            is_published=True
        ).select_related('teacher').prefetch_related('topics')[:6]
        
        # Recent Conversations (last 5)
        recent_conversations_raw = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants').order_by('-updated_at')[:5]
        
        # Add other participant info to each conversation
        recent_conversations = []
        for conv in recent_conversations_raw:
            other_user = conv.get_other_participant(user)
            recent_conversations.append({
                'conversation': conv,
                'other_user': other_user,
                'latest_message': conv.get_latest_message(),
            })
        
        # Teaching Stats (if user is a teacher)
        teaching_classes = TeachingClass.objects.filter(teacher=user, is_published=True)
        if teaching_classes.exists():
            teaching_stats = {
                'total_classes': teaching_classes.count(),
                'total_students': ClassEnrollment.objects.filter(
                    teaching_class__teacher=user,
                    status=ClassEnrollment.ACTIVE
                ).values('user').distinct().count(),
                'upcoming_teaching_sessions': ClassBooking.objects.filter(
                    time_slot__teaching_class__teacher=user,
                    status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING],
                    time_slot__start_time__gte=timezone.now()
                ).select_related(
                    'time_slot',
                    'time_slot__teaching_class',
                    'student'
                ).order_by('time_slot__start_time')[:5],
            }

    # Matched Classes (whitelisted classes - classes user swiped right on)
    matched_classes = []
    if user:
        whitelisted_class_ids = SwipeAction.objects.filter(
            user=user,
            action=SwipeAction.SWIPE_RIGHT
        ).values_list('teaching_class_id', flat=True)[:5]
        
        matched_classes = TeachingClass.objects.filter(
            id__in=whitelisted_class_ids,
            is_published=True
        ).select_related('teacher').prefetch_related('topics')
    
    # Trending Classes (most enrollments in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    trending_classes = TeachingClass.objects.filter(
        is_published=True,
        enrollments__created_at__gte=thirty_days_ago
    ).annotate(
        recent_enrollments=Count('enrollments', filter=Q(enrollments__created_at__gte=thirty_days_ago))
    ).select_related('teacher').prefetch_related('topics').order_by(
        '-recent_enrollments', '-avg_rating'
    ).distinct()[:6]

    context = {
        'featured_skills': featured_skills,
        'user_communities': user_communities,
        'recent_matches': recent_matches,
        'matched_users': matched_users,
        'dashboard_stats': dashboard_stats,
        'upcoming_sessions': upcoming_sessions,
        'recommended_classes': recommended_classes,
        'recent_conversations': recent_conversations,
        'teaching_stats': teaching_stats,
        'matched_classes': matched_classes,
        'trending_classes': trending_classes,
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
        ).filter(
            is_active=True  # Only show active users
        ).select_related('profile').distinct().order_by('username')[:10]
    
    # Search skills with teacher counts
    skill_results = []
    if q:
        skill_results = Skill.objects.filter(name__icontains=q).annotate(
            teachers_count=Count('userskill', filter=Q(userskill__can_teach=True))
        )[:10]
    
    # Search classes (exclude soft-deleted)
    class_results = []
    if q:
        classes = TeachingClass.objects.filter(
            Q(title__icontains=q) |
            Q(short_description__icontains=q) |
            Q(full_description__icontains=q),
            is_published=True  # Only show published classes
        ).select_related('teacher').order_by('-created_at')[:10]
        
        # Add formatted price to each class
        for cls in classes:
            cls.price_formatted = f"${cls.price_cents / 100:.2f}" if cls.price_cents and cls.price_cents > 0 else "Free"
        
        class_results = classes
    
    # Search communities
    community_results = Community.objects.filter(name__icontains=q)[:10] if q else []
    
    # Calculate total results count
    total_results = len(user_results) + len(skill_results) + len(class_results) + len(community_results)
    
    return render(request, 'core/search.html', {
        'q': q,
        'user_results': user_results,
        'skill_results': skill_results,
        'class_results': class_results,
        'community_results': community_results,
        'total_results': total_results,
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
    
@login_required
def report_content(request):
    """Main report page - allows reporting any content"""
    if request.method == 'POST':
        content_type_id = request.POST.get('content_type')
        object_id = request.POST.get('object_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        
        if not all([content_type_id, object_id, reason, description]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('core:report_content')
        
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            
            # Verify the object exists
            model_class = content_type.model_class()
            reported_obj = get_object_or_404(model_class, id=object_id)
            
            # Create the report (pending admin review)
            report = Report.objects.create(
                reporter=request.user,
                content_type=content_type,
                object_id=object_id,
                reason=reason,
                description=description,
                status='pending'  # Pending admin review
            )
            
            messages.success(request, 'Thank you for your report. Our team will review it shortly.')
            return redirect('core:home')
            
        except Exception as e:
            messages.error(request, f'Error submitting report: {str(e)}')
            return redirect('core:report_content')
    
    # Get available content types for reporting
    reportable_models = ['user', 'community', 'teachingclass', 'post']
    content_types = ContentType.objects.filter(model__in=reportable_models)
    
    # Get content type IDs for template
    content_type_map = {}
    for ct in content_types:
        content_type_map[ct.model] = ct.id
    
    # Get all users, communities, classes, posts for selection (exclude soft-deleted)
    users = User.objects.exclude(id=request.user.id).filter(is_active=True).order_by('username')[:100]
    
    from communities.models import Community, Post
    communities = Community.objects.all().order_by('name')[:100]
    posts = Post.objects.all().order_by('-created_at')[:100]
    
    from skills.models import TeachingClass
    classes = TeachingClass.objects.filter(is_published=True).order_by('title')[:100]
    
    context = {
        'content_types': content_types,
        'content_type_map': content_type_map,
        'users': users,
        'communities': communities,
        'classes': classes,
        'posts': posts,
    }
    
    return render(request, 'core/report_content.html', context)


@login_required
def quick_report(request, content_type, object_id):
    """Quick report with pre-filled content type and object"""
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description')
        
        if not all([reason, description]):
            messages.error(request, 'Please fill in all fields.')
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
        
        try:
            ct = ContentType.objects.get(model=content_type)
            
            # Verify the object exists
            model_class = ct.model_class()
            reported_obj = get_object_or_404(model_class, id=object_id)
            
            # Create the report (pending admin review)
            report = Report.objects.create(
                reporter=request.user,
                content_type=ct,
                object_id=object_id,
                reason=reason,
                description=description,
                status='pending'  # Pending admin review
            )
            
            messages.success(request, 'Report submitted successfully. Our team will review it shortly.')
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
    
    return redirect('core:report_content')


@login_required
def user_reports(request):
    """View user's own reports"""
    reports = Report.objects.filter(reporter=request.user).select_related(
        'content_type', 'reviewed_by'
    )
    
    return render(request, 'core/user_reports.html', {'reports': reports})


# ADMIN VIEWS
@login_required
def admin_reports(request):
    """Admin page to review all reports"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('core:home')
    
    status_filter = request.GET.get('status', 'pending')
    
    reports = Report.objects.select_related(
        'reporter', 'content_type', 'reviewed_by'
    ).order_by('-created_at')
    
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)
    
    # Get counts for each status
    status_counts = {
        'all': Report.objects.count(),
        'pending': Report.objects.filter(status='pending').count(),
        'investigating': Report.objects.filter(status='investigating').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'dismissed': Report.objects.filter(status='dismissed').count(),
    }
    
    context = {
        'reports': reports,
        'status_filter': status_filter,
        'status_counts': status_counts,
    }
    
    return render(request, 'core/admin_reports.html', context)


@login_required
def custom_admin(request):
    """Custom admin page that looks like Django admin but with custom HTML"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('core:home')
    
    # Get all models and their counts
    admin_sections = [
        {
            'name': 'Users & Profiles',
            'models': [
                {'name': 'Users', 'count': User.objects.count(), 'url': '/admin/auth/user/'},
                {'name': 'Profiles', 'count': Profile.objects.count(), 'url': '/admin/users/profile/'},
                {'name': 'Evidence', 'count': Evidence.objects.count(), 'url': '/admin/users/evidence/'},
                {'name': 'Identity Submissions', 'count': IdentitySubmission.objects.count(), 'url': '/admin/users/identitysubmission/'},
            ]
        },
        {
            'name': 'Skills & Classes',
            'models': [
                {'name': 'Skills', 'count': Skill.objects.count(), 'url': '/admin/skills/skill/'},
                {'name': 'User Skills', 'count': UserSkill.objects.count(), 'url': '/admin/skills/userskill/'},
                {'name': 'Teaching Classes', 'count': TeachingClass.objects.count(), 'url': '/admin/skills/teachingclass/'},
                {'name': 'Class Enrollments', 'count': ClassEnrollment.objects.count(), 'url': '/admin/skills/classenrollment/'},
                {'name': 'Class Bookings', 'count': ClassBooking.objects.count(), 'url': '/admin/skills/classbooking/'},
                {'name': 'Class Reviews', 'count': ClassReview.objects.count(), 'url': '/admin/skills/classreview/'},
                {'name': 'Teacher Applications', 'count': TeacherApplication.objects.count(), 'url': '/admin/skills/teacherapplication/'},
            ]
        },
        {
            'name': 'Communities',
            'models': [
                {'name': 'Communities', 'count': Community.objects.count(), 'url': '/admin/communities/community/'},
                {'name': 'Community Requests', 'count': CommunityRequest.objects.count(), 'url': '/admin/communities/communityrequest/'},
                {'name': 'Posts', 'count': Post.objects.count(), 'url': '/admin/communities/post/'},
                {'name': 'Comments', 'count': Comment.objects.count(), 'url': '/admin/communities/comment/'},
            ]
        },
        {
            'name': 'Messaging',
            'models': [
                {'name': 'Conversations', 'count': Conversation.objects.count(), 'url': '/admin/chat/conversation/'},
                {'name': 'Messages', 'count': Message.objects.count(), 'url': '/admin/chat/message/'},
                {'name': 'Message Status', 'count': MessageStatus.objects.count(), 'url': '/admin/chat/messagestatus/'},
            ]
        },
        {
            'name': 'Reports & Moderation',
            'models': [
                {'name': 'Reports', 'count': Report.objects.count(), 'url': '/admin/core/report/'},
                {'name': 'User Warnings', 'count': UserWarning.objects.count(), 'url': '/admin/core/userwarning/'},
            ]
        },
    ]
    
    context = {
        'admin_sections': admin_sections,
    }
    
    return render(request, 'core/custom_admin.html', context)


@login_required
@require_http_methods(["POST"])
def admin_handle_report(request, report_id):
    """Admin action to handle a specific report"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        report = get_object_or_404(Report, id=report_id)
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'dismiss':
            report.status = 'dismissed'
            report.action_taken = 'none'
            
        elif action == 'warning':
            report.status = 'resolved'
            report.action_taken = 'warning'
            
            # Issue warning to the reported user
            if report.content_type.model == 'user':
                reported_user = report.reported_object
                UserWarning.objects.create(
                    user=reported_user,
                    issued_by=request.user,
                    related_report=report,
                    reason=report.get_reason_display(),
                    description=admin_notes or report.description
                )
                messages.success(request, f'Warning issued to {reported_user.username}')
            
        elif action == 'remove_content':
            report.status = 'resolved'
            report.action_taken = 'content_removed'
            
            # Soft delete the reported content (only when admin explicitly approves)
            try:
                reported_obj = report.reported_object
                if reported_obj:
                    if report.content_type.model == 'user':
                        # For users, deactivate (soft delete) - only when admin approves removal
                        if reported_obj.is_active:
                            reported_obj.is_active = False
                            reported_obj.save()
                            messages.success(request, f'User {reported_obj.username} has been deactivated (can be restored).')
                        else:
                            messages.warning(request, f'User {reported_obj.username} is already deactivated.')
                    else:
                        # Hard delete for posts, communities, classes
                        reported_obj.delete()
                        messages.success(request, 'Content removed successfully.')
            except Exception as e:
                messages.error(request, f'Could not remove content: {str(e)}')
                
        elif action == 'suspend_user':
            report.status = 'resolved'
            report.action_taken = 'user_suspended'
            
            if report.content_type.model == 'user':
                reported_user = report.reported_object
                reported_user.is_active = False
                reported_user.save()
                messages.success(request, f'User {reported_user.username} suspended.')
        
        report.admin_notes = admin_notes
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.save()
        
        messages.success(request, 'Report handled successfully.')
        return redirect('core:admin_reports')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('core:admin_reports')


@login_required
@require_http_methods(["POST"])
def admin_restore_content(request, content_type, object_id):
    """Admin action to restore soft-deleted content or reactivate users"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        ct = ContentType.objects.get(model=content_type)
        model_class = ct.model_class()
        content_obj = get_object_or_404(model_class, id=object_id)
        
        if content_type == 'user':
            # For users, reactivate them
            if not content_obj.is_active:
                content_obj.is_active = True
                content_obj.save()
                messages.success(request, f'User {content_obj.username} has been reactivated.')
            else:
                messages.warning(request, 'User is already active.')
        else:
            messages.warning(request, 'Content restoration is not available for this content type.')
        
        return redirect('core:admin_reports')
        
    except Exception as e:
        messages.error(request, f'Error restoring content: {str(e)}')
        return redirect('core:admin_reports')
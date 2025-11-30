# users/context_processors.py
from django.conf import settings
from django.db.models import Count, Q

def recaptcha_site_key(request):
    """
    Add reCAPTCHA site key to all template contexts.
    This allows you to use {{ RECAPTCHA_SITE_KEY }} in any template.
    """
    return {
        'RECAPTCHA_SITE_KEY': getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    }

def unread_messages_count(request):
    """
    Add unread message count to all template contexts.
    This allows you to use {{ unread_messages_count }} in any template.
    """
    unread_count = 0
    if request.user.is_authenticated:
        from chat.models import MessageStatus
        unread_count = MessageStatus.objects.filter(
            user=request.user,
            is_read=False
        ).exclude(
            message__sender=request.user
        ).count()
    
    return {
        'unread_messages_count': unread_count
    }

def sidebar_data(request):
    """
    Add dynamic sidebar data to all template contexts.
    Includes recent communities, trending classes, and quick stats.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from collections import Counter
        from communities.models import Community
        from skills.models import TeachingClass, ClassEnrollment
        from users.models import UserSkill
        
        sidebar_info = {
            'recent_communities': [],
            'trending_classes': [],
            'sidebar_stats': {},
        }
        
        if request.user.is_authenticated:
            user = request.user
            
            # Recent communities (user's communities, limit 5)
            try:
                sidebar_info['recent_communities'] = list(Community.objects.filter(
                    members=user
                ).order_by('-created_at')[:5])
            except Exception:
                sidebar_info['recent_communities'] = []
            
            # Trending classes (most enrollments in last 7 days, limit 5)
            try:
                seven_days_ago = timezone.now() - timedelta(days=7)
                # Get recent enrollments first
                recent_enrollment_ids = list(ClassEnrollment.objects.filter(
                    created_at__gte=seven_days_ago,
                    status='active'
                ).values_list('teaching_class_id', flat=True))
                
                if recent_enrollment_ids:
                    # Count enrollments per class
                    class_counts = Counter(recent_enrollment_ids)
                    
                    # Get top 5 class IDs
                    top_class_ids = [class_id for class_id, count in class_counts.most_common(5)]
                    
                    # Get the classes
                    trending_classes = TeachingClass.objects.filter(
                        id__in=top_class_ids,
                        is_published=True
                    ).order_by('-created_at')[:5]
                    sidebar_info['trending_classes'] = list(trending_classes)
                else:
                    # No recent enrollments, just get recent published classes
                    sidebar_info['trending_classes'] = list(TeachingClass.objects.filter(
                        is_published=True
                    ).order_by('-created_at')[:5])
            except Exception:
                # Fallback: just get recent published classes
                sidebar_info['trending_classes'] = list(TeachingClass.objects.filter(
                    is_published=True
                ).order_by('-created_at')[:5])
            
            # Quick stats
            try:
                sidebar_info['sidebar_stats'] = {
                    'enrolled_classes': ClassEnrollment.objects.filter(
                        user=user,
                        status='active'
                    ).count(),
                    'teaching_skills': UserSkill.objects.filter(
                        user=user,
                        can_teach=True
                    ).count(),
                    'learning_skills': UserSkill.objects.filter(
                        user=user,
                        wants_to_learn=True
                    ).count(),
                    'communities_count': Community.objects.filter(members=user).count(),
                }
            except Exception:
                sidebar_info['sidebar_stats'] = {}
        else:
            # For non-authenticated users, show trending classes
            try:
                seven_days_ago = timezone.now() - timedelta(days=7)
                # Get recent enrollments first
                recent_enrollment_ids = list(ClassEnrollment.objects.filter(
                    created_at__gte=seven_days_ago,
                    status='active'
                ).values_list('teaching_class_id', flat=True))
                
                if recent_enrollment_ids:
                    # Count enrollments per class
                    class_counts = Counter(recent_enrollment_ids)
                    
                    # Get top 5 class IDs
                    top_class_ids = [class_id for class_id, count in class_counts.most_common(5)]
                    
                    # Get the classes
                    trending_classes = TeachingClass.objects.filter(
                        id__in=top_class_ids,
                        is_published=True
                    ).order_by('-created_at')[:5]
                    sidebar_info['trending_classes'] = list(trending_classes)
                else:
                    # No recent enrollments, just get recent published classes
                    sidebar_info['trending_classes'] = list(TeachingClass.objects.filter(
                        is_published=True
                    ).order_by('-created_at')[:5])
            except Exception:
                # Fallback: just get recent published classes
                sidebar_info['trending_classes'] = list(TeachingClass.objects.filter(
                    is_published=True
                ).order_by('-created_at')[:5])
        
        return sidebar_info
    except Exception as e:
        # Return empty data if anything fails to prevent 500 errors
        return {
            'recent_communities': [],
            'trending_classes': [],
            'sidebar_stats': {},
        }
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.text import slugify
from skills.models import TeacherApplication, TeachingClass

# Create your views here.

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def skill_review(request):
    """Re-purposed: Admin view to review teacher applications (pending)."""
    pending_apps = TeacherApplication.objects.filter(status=TeacherApplication.PENDING).select_related('applicant')
    context = {
        'applications': pending_apps,
        'total_pending': pending_apps.count(),
    }
    return render(request, 'admin/skill_review.html', context)

@user_passes_test(is_admin)
def skill_detail(request, user_id=None, skill_id=None, application_id=None):
    """Re-purposed: Review a specific teacher application."""
    application = get_object_or_404(TeacherApplication, id=application_id) if application_id else None
    user = application.applicant if application else None
    context = {
        'application': application,
        'user': user,
    }
    return render(request, 'admin/skill_detail.html', context)

@user_passes_test(is_admin)
def verify_skill(request, user_id=None, skill_id=None, application_id=None):
    """Re-purposed: Approve a teacher application."""
    if request.method == 'POST':
        from django.db import transaction
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            application = get_object_or_404(TeacherApplication, id=application_id)
            notes = request.POST.get('verification_message', '').strip()
            
            # Use transaction to ensure both saves happen together
            with transaction.atomic():
                application.status = TeacherApplication.APPROVED
                application.decision_notes = notes
                application.reviewer = request.user
                application.reviewed_at = timezone.now()
                application.save()
                
                # Auto-create a TeachingClass using application data
                base_slug = slugify(application.title) or f"class-{application.id}"
                unique_slug = base_slug
                i = 1
                while TeachingClass.objects.filter(slug=unique_slug).exists():
                    i += 1
                    unique_slug = f"{base_slug}-{i}"
                
                # Check if publish checkbox is checked
                # HTML checkboxes: if checked, sends 'on'; if unchecked, not in POST
                is_published = request.POST.get('is_published') == 'on'
                
                # Difficulty and tradeable/price/duration come from the user's application by default
                post_is_trade = request.POST.get('is_tradeable')
                is_tradeable = (post_is_trade == 'on') if post_is_trade is not None else application.is_tradeable
                difficulty = (request.POST.get('difficulty') or application.difficulty or 'beginner')
                try:
                    duration_minutes = int((request.POST.get('duration_minutes') if request.POST.get('duration_minutes') is not None else application.duration_minutes) or 0)
                except Exception:
                    duration_minutes = 0
                try:
                    price_cents = int((request.POST.get('price_cents') if request.POST.get('price_cents') is not None else application.price_cents) or 0)
                except Exception:
                    price_cents = 0

                teaching_class = TeachingClass.objects.create(
                    teacher=application.applicant,
                    title=application.title,
                    slug=unique_slug,
                    short_description=(application.bio or '')[:140],
                    full_description=application.bio or '',
                    intro_video=application.intro_video,
                    thumbnail=application.thumbnail,
                    is_published=is_published,
                    is_tradeable=is_tradeable,
                    difficulty=difficulty,
                    duration_minutes=duration_minutes,
                    price_cents=price_cents,
                )
                
                # Force refresh from database to ensure it's saved
                teaching_class.refresh_from_db()
                
                # Log the creation for debugging
                logger.info(f"Created TeachingClass: ID={teaching_class.id}, Title={teaching_class.title}, Published={teaching_class.is_published}, Teacher={teaching_class.teacher.username}")
                print(f"DEBUG: Created class {teaching_class.id} - {teaching_class.title} (published={teaching_class.is_published})")
                
            # Verify the class exists after transaction
            if not TeachingClass.objects.filter(id=teaching_class.id).exists():
                logger.error(f"ERROR: Class {teaching_class.id} was not saved to database!")
                messages.error(request, 'Error: Class was not saved. Please check database connection.')
            else:
                messages.success(request, f'Approved teacher application for {application.applicant.username}. Class created successfully.')
                
        except Exception as e:
            logger.error(f"Error creating class: {str(e)}", exc_info=True)
            print(f"ERROR creating class: {str(e)}")
            messages.error(request, f'Error creating class: {str(e)}')
            return redirect('skill_admin:skill_detail', application_id=application_id)
            
        return redirect('skill_admin:skill_review')
    return redirect('skill_admin:skill_detail', application_id=application_id)

@user_passes_test(is_admin)
def reject_skill(request, user_id=None, skill_id=None, application_id=None):
    """Re-purposed: Reject a teacher application."""
    if request.method == 'POST':
        application = get_object_or_404(TeacherApplication, id=application_id)
        notes = request.POST.get('verification_message', '').strip()
        application.status = TeacherApplication.REJECTED
        application.decision_notes = notes
        application.reviewer = request.user
        from django.utils import timezone
        application.reviewed_at = timezone.now()
        application.save()
        messages.info(request, f'Rejected teacher application for {application.applicant.username}.')
        return redirect('skill_admin:skill_review')
    return redirect('skill_admin:skill_detail', application_id=application_id)
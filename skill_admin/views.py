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
            
            # Check if this is an edit request BEFORE overwriting decision_notes
            original_decision_notes = str(application.decision_notes or "")
            is_edit_request = "EDIT REQUEST for existing class:" in original_decision_notes
            
            # Extract edit request info before it gets overwritten
            existing_class = None
            if is_edit_request:
                import re
                match = re.search(r'EDIT REQUEST for existing class:\s*(\S+?)\s+\(ID:\s*(\d+)\)', original_decision_notes)
                if match:
                    class_slug = match.group(1).strip()
                    class_id = int(match.group(2))
                    try:
                        existing_class = TeachingClass.objects.get(id=class_id, slug=class_slug)
                        logger.info(f"Found existing class for edit request: ID={class_id}, slug={class_slug}, title='{existing_class.title}'")
                    except TeachingClass.DoesNotExist:
                        logger.warning(f"Edit request references non-existent class ID {class_id}, slug '{class_slug}'. Creating new class instead.")
                        is_edit_request = False
                    except TeachingClass.MultipleObjectsReturned:
                        existing_class = TeachingClass.objects.filter(id=class_id, slug=class_slug).first()
                else:
                    # Try fallback: extract just ID
                    id_match = re.search(r'\(ID:\s*(\d+)\)', original_decision_notes)
                    if id_match:
                        class_id = int(id_match.group(1))
                        try:
                            existing_class = TeachingClass.objects.get(id=class_id)
                            logger.info(f"Found existing class by ID only: ID={class_id}")
                        except TeachingClass.DoesNotExist:
                            is_edit_request = False
            
            notes = request.POST.get('verification_message', '').strip()
            
            # Use transaction to ensure both saves happen together
            with transaction.atomic():
                application.status = TeacherApplication.APPROVED
                # Preserve edit request info in decision_notes, append admin notes if provided
                if is_edit_request and existing_class:
                    if notes:
                        application.decision_notes = f"{original_decision_notes}\n\nAdmin Notes: {notes}"
                    else:
                        application.decision_notes = original_decision_notes
                else:
                    application.decision_notes = notes
                application.reviewer = request.user
                application.reviewed_at = timezone.now()
                application.save()
                
                # We already checked for edit request and extracted existing_class above
                logger.info(f"Processing application {application.id}. is_edit_request={is_edit_request}, existing_class={existing_class}")
                
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

                if is_edit_request and existing_class:
                    # Update existing class - preserve slug to avoid breaking URLs
                    existing_class.title = application.title
                    existing_class.short_description = (application.bio or existing_class.short_description or '')[:300]
                    existing_class.full_description = application.bio or existing_class.full_description or ''
                    # Only update files if new ones were provided
                    if application.intro_video:
                        existing_class.intro_video = application.intro_video
                    if application.thumbnail:
                        existing_class.thumbnail = application.thumbnail
                    existing_class.is_published = is_published
                    existing_class.is_tradeable = is_tradeable
                    existing_class.difficulty = difficulty
                    existing_class.duration_minutes = duration_minutes
                    existing_class.price_cents = price_cents
                    # Slug is preserved - don't change it even if title changed
                    existing_class.save()
                    
                    teaching_class = existing_class
                    logger.info(f"Updated TeachingClass: ID={teaching_class.id}, Title={teaching_class.title}, Slug={teaching_class.slug}, Published={teaching_class.is_published}")
                    print(f"DEBUG: Updated existing class {teaching_class.id} - {teaching_class.title} (slug={teaching_class.slug}, published={teaching_class.is_published})")
                else:
                    # Create new class
                    base_slug = slugify(application.title) or f"class-{application.id}"
                    unique_slug = base_slug
                    i = 1
                    while TeachingClass.objects.filter(slug=unique_slug).exists():
                        i += 1
                        unique_slug = f"{base_slug}-{i}"

                    teaching_class = TeachingClass.objects.create(
                        teacher=application.applicant,
                        title=application.title,
                        slug=unique_slug,
                        short_description=(application.bio or '')[:300],
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
                if is_edit_request and existing_class:
                    messages.success(request, f'Approved class edit application for {application.applicant.username}. Class updated successfully.')
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
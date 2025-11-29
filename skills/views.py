from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Count, Q, Avg
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages

from .models import TeachingClass, ClassTopic, ClassReview, ClassEnrollment, ClassTradeOffer, TeacherApplication, ClassTimeSlot, ClassBooking, ClassFavorite
from django.db.models import Avg
from chat.views import get_or_create_conversation
from chat.models import Message
from decimal import Decimal, InvalidOperation
import json


class ClassListView(ListView):
    template_name = 'skills/classes_list.html'
    context_object_name = 'classes'
    paginate_by = 12

    def get_queryset(self):
        qs = TeachingClass.objects.filter(is_published=True).select_related('teacher').prefetch_related('topics')
        
        # Search query
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        
        # Difficulty filter
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        
        # Price filter
        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                max_price_cents = int(float(max_price) * 100)
                qs = qs.filter(price_cents__lte=max_price_cents)
            except (ValueError, TypeError):
                pass
        
        # Duration filter
        max_duration = self.request.GET.get('max_duration')
        if max_duration:
            try:
                qs = qs.filter(duration_minutes__lte=int(max_duration))
            except (ValueError, TypeError):
                pass
        
        # Tradeable filter
        tradeable_only = self.request.GET.get('tradeable')
        if tradeable_only == 'true':
            qs = qs.filter(is_tradeable=True)
        
        # Topic filter
        topic = self.request.GET.get('topic')
        if topic:
            qs = qs.filter(topics__name__icontains=topic).distinct()
        
        # Sort options
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'rating':
            qs = qs.order_by('-avg_rating', '-reviews_count')
        elif sort_by == 'price_low':
            qs = qs.order_by('price_cents')
        elif sort_by == 'price_high':
            qs = qs.order_by('-price_cents')
        elif sort_by == 'trending':
            # Trending: classes with most enrollments in last 30 days
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            qs = qs.annotate(
                recent_enrollments=models.Count(
                    'enrollments',
                    filter=models.Q(enrollments__created_at__gte=thirty_days_ago)
                )
            ).order_by('-recent_enrollments', '-avg_rating')
        else:  # newest (default)
            qs = qs.order_by('-created_at')
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all unique topics for filter
        context['all_topics'] = ClassTopic.objects.values_list('name', flat=True).distinct().order_by('name')
        
        # Check which classes are favorited by user
        if self.request.user.is_authenticated:
            favorited_ids = ClassFavorite.objects.filter(
                user=self.request.user
            ).values_list('teaching_class_id', flat=True)
            context['favorited_class_ids'] = set(favorited_ids)
        else:
            context['favorited_class_ids'] = set()
        
        return context


class ClassDetailView(DetailView):
    template_name = 'skills/class_detail.html'
    context_object_name = 'cls'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    queryset = TeachingClass.objects.select_related('teacher').prefetch_related('topics', 'reviews__reviewer')

    def get(self, request, *args, **kwargs):
        """Handle payment success redirect before rendering"""
        self.object = self.get_object()
        user = request.user
        
        # Handle payment success - redirect to book session page immediately
        if request.GET.get('paid') == '1' and user.is_authenticated:
            cls = self.object
            session_id = request.GET.get('session_id')
            
            # Check if we've already processed this payment (prevent duplicate messages)
            session_key = f'payment_processed_{session_id}' if session_id else f'payment_processed_{cls.id}'
            if not request.session.get(session_key):
                # Verify payment and enroll if webhook didn't fire
                enrollment = ClassEnrollment.objects.filter(
                    user=user,
                    teaching_class=cls,
                    status=ClassEnrollment.ACTIVE
                ).first()
                
                if not enrollment:
                    try:
                        # Delete any revoked enrollments first (for re-enrollment)
                        ClassEnrollment.objects.filter(
                            user=user,
                            teaching_class=cls,
                            status=ClassEnrollment.REVOKED
                        ).delete()
                        
                        # Verify and create enrollment
                        self._verify_and_enroll_from_payment(user, cls)
                        
                        # Check again after verification
                        enrollment = ClassEnrollment.objects.filter(
                            user=user,
                            teaching_class=cls,
                            status=ClassEnrollment.ACTIVE
                        ).first()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Error verifying payment: {e}")
                
                # Only redirect if enrollment exists
                if enrollment:
                    messages.success(request, f'Payment successful! You are now enrolled in "{cls.title}". You can now book your sessions.')
                    # Mark as processed to prevent duplicate messages
                    request.session[session_key] = True
                    # Redirect to clean URL without parameters
                    return HttpResponseRedirect(reverse('skills:view_schedule', args=[cls.slug]))
                else:
                    # Enrollment not ready yet, show message and stay on page
                    messages.warning(request, 'Payment received! Your enrollment is being processed. Please wait a moment and refresh the page.')
            else:
                # Already processed, redirect to clean URL
                return HttpResponseRedirect(reverse('skills:view_schedule', args=[cls.slug]))
        
        # Continue with normal rendering
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cls = self.object
        is_enrolled = False
        enrollment = None
        is_completed = False
        is_favorited = False
        
        if user.is_authenticated:
            # Check for active enrollment
            enrollment = ClassEnrollment.objects.filter(
                user=user, 
                teaching_class=cls, 
                status=ClassEnrollment.ACTIVE
            ).first()
            is_enrolled = enrollment is not None
            
            # Check if enrollment should be revoked (all sessions completed)
            if enrollment:
                # Check and revoke if all sessions are completed
                enrollment.check_and_revoke_if_complete()
                # Re-fetch to get updated status
                enrollment.refresh_from_db()
                is_enrolled = enrollment.is_active()
                is_completed = not is_enrolled and enrollment.status == ClassEnrollment.REVOKED
            else:
                # Check if there's a revoked enrollment (completed class)
                revoked_enrollment = ClassEnrollment.objects.filter(
                    user=user,
                    teaching_class=cls,
                    status=ClassEnrollment.REVOKED
                ).first()
                if revoked_enrollment:
                    is_completed = True
                    is_enrolled = False
            
            is_favorited = ClassFavorite.objects.filter(user=user, teaching_class=cls).exists()
        
        # Handle payment cancellation and errors
        if self.request.GET.get('cancel') == '1':
            messages.info(self.request, 'Payment was cancelled. You can try again anytime.')
        elif self.request.GET.get('error') == 'stripe_not_configured':
            messages.error(self.request, 'Payment system is not configured. Please contact support.')
        elif self.request.GET.get('error') == 'stripe_not_installed':
            messages.error(self.request, 'Payment system is not available. Please contact support.')
        elif self.request.GET.get('error') == 'pricing_required':
            messages.error(self.request, 'This class requires payment to enroll.')
        
        context['is_enrolled'] = is_enrolled
        context['enrollment'] = enrollment
        context['is_completed'] = is_completed
        context['is_favorited'] = is_favorited
        return context
    
    def _verify_and_enroll_from_payment(self, user, cls):
        """Fallback: Verify payment and enroll user if payment was successful but webhook didn't fire"""
        try:
            import stripe
            secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not secret:
                return
            
            stripe.api_key = secret
            
            # Try to get session_id from URL first (more reliable)
            session_id = self.request.GET.get('session_id')
            
            if session_id:
                # Verify the specific session
                try:
                    session = stripe.checkout.Session.retrieve(session_id)
                    
                    # Verify it's for this user and class
                    metadata = session.get('metadata', {})
                    class_id = metadata.get('class_id')
                    user_id = metadata.get('user_id')
                    
                    if (class_id and str(cls.id) == class_id and 
                        user_id and str(user.id) == user_id and
                        session.get('payment_status') == 'paid'):
                        
                        # Payment was successful, create enrollment
                        self._create_enrollment_from_session(user, cls, session, metadata)
                        return
                except stripe.error.StripeError:
                    pass
            
            # Fallback: Search recent sessions if session_id not available
            from datetime import datetime, timedelta
            sessions = stripe.checkout.Session.list(
                limit=10,
                created={'gte': int((datetime.now() - timedelta(hours=1)).timestamp())},
            )
            
            for session in sessions.data:
                metadata = session.get('metadata', {})
                class_id = metadata.get('class_id')
                user_id = metadata.get('user_id')
                
                # Check if this session matches our class and user
                if (class_id and str(cls.id) == class_id and 
                    user_id and str(user.id) == user_id and
                    session.get('payment_status') == 'paid'):
                    
                    self._create_enrollment_from_session(user, cls, session, metadata)
                    break
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in payment verification fallback: {e}")
    
    def _create_enrollment_from_session(self, user, cls, session, metadata):
        """Helper method to create enrollment from a Stripe session"""
        try:
            # Payment was successful, create enrollment
            enrollment, created = ClassEnrollment.objects.update_or_create(
                user=user,
                teaching_class=cls,
                defaults={
                    'status': ClassEnrollment.ACTIVE,
                    'granted_via': ClassEnrollment.PURCHASE,
                    'purchase_id': session.get('payment_intent') or session.get('id')
                },
            )
            
            # Create booking if time_slot_id was provided
            time_slot_id = metadata.get('time_slot_id')
            booking_notes = metadata.get('booking_notes', '')
            
            if time_slot_id and enrollment:
                try:
                    time_slot = ClassTimeSlot.objects.get(id=time_slot_id, teaching_class=cls)
                    if not time_slot.is_fully_booked() and time_slot.start_time > timezone.now():
                        ClassBooking.objects.get_or_create(
                            time_slot=time_slot,
                            student=user,
                            enrollment=enrollment,
                            defaults={
                                'status': ClassBooking.CONFIRMED,
                                'notes': booking_notes,
                            }
                        )
                except ClassTimeSlot.DoesNotExist:
                    pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating enrollment from session: {e}")


class ClassReviewCreateView(LoginRequiredMixin, View):
    def post(self, request, slug):
        teaching_class = get_object_or_404(TeachingClass, slug=slug, is_published=True)
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        if 1 <= rating <= 5:
            review, created = ClassReview.objects.update_or_create(
                teaching_class=teaching_class,
                reviewer=request.user,
                defaults={"rating": rating, "comment": comment},
            )
            # Update aggregates (simple recalculation)
            agg = ClassReview.objects.filter(teaching_class=teaching_class).aggregate_avg = None
            reviews = ClassReview.objects.filter(teaching_class=teaching_class)
            count = reviews.count()
            avg = round(sum(r.rating for r in reviews) / count, 2) if count else 0
            TeachingClass.objects.filter(pk=teaching_class.pk).update(avg_rating=avg, reviews_count=count)
        return HttpResponseRedirect(reverse('skills:class_detail', args=[teaching_class.slug]))


class ClassTradeProposeView(LoginRequiredMixin, View):
    def post(self, request, slug):
        requested_class = get_object_or_404(TeachingClass, slug=slug, is_published=True)
        offered_id = request.POST.get('offered_class_id')
        message = request.POST.get('message', '').strip()
        if not offered_id:
            messages.error(request, 'Please select a class to offer.')
            return HttpResponseRedirect(reverse('skills:class_detail', args=[requested_class.slug]))
        offered_class = get_object_or_404(TeachingClass, pk=offered_id, teacher=request.user)
        
        # Check if there's already a pending offer
        existing = ClassTradeOffer.objects.filter(
            proposer=request.user,
            receiver=requested_class.teacher,
            requested_class=requested_class,
            offered_class=offered_class,
            status=ClassTradeOffer.PENDING
        ).first()
        
        if existing:
            messages.info(request, 'You already have a pending trade offer for this class.')
        else:
            trade_offer = ClassTradeOffer.objects.create(
                proposer=request.user,
                receiver=requested_class.teacher,
                offered_class=offered_class,
                requested_class=requested_class,
                message=message,
            )
            messages.success(request, 'Trade offer sent successfully!')
            
            # Create a message in the chat system
            conversation = get_or_create_conversation(request.user, requested_class.teacher)
            message_content = f"Hi! I'd like to propose a trade: I'll offer my class '{offered_class.title}' in exchange for your class '{requested_class.title}'."
            if message:
                message_content += f"\n\nNote: {message}"
            message_content += f"\n\nView the trade offer: {request.build_absolute_uri(reverse('skills:trade_offers'))}"
            
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=message_content
            )
        return HttpResponseRedirect(reverse('skills:class_detail', args=[requested_class.slug]))


class TradeOffersListView(LoginRequiredMixin, View):
    """View to list all trade offers (received and sent)"""
    template_name = 'skills/trade_offers.html'
    
    def get(self, request):
        # Get filter parameter (show all or only active)
        show_all = request.GET.get('show_all', 'false').lower() == 'true'
        
        # Get received trade offers (offers where user is the receiver)
        received_queryset = ClassTradeOffer.objects.filter(
            receiver=request.user
        ).select_related('proposer', 'offered_class', 'requested_class')
        
        # Filter out declined/cancelled if not showing all
        if not show_all:
            received_queryset = received_queryset.exclude(
                status__in=[ClassTradeOffer.DECLINED, ClassTradeOffer.CANCELLED]
            )
        
        received_offers = received_queryset.order_by('-created_at')
        
        # Get sent trade offers (offers where user is the proposer)
        sent_queryset = ClassTradeOffer.objects.filter(
            proposer=request.user
        ).select_related('receiver', 'offered_class', 'requested_class')
        
        # Filter out declined/cancelled if not showing all
        if not show_all:
            sent_queryset = sent_queryset.exclude(
                status__in=[ClassTradeOffer.DECLINED, ClassTradeOffer.CANCELLED]
            )
        
        sent_offers = sent_queryset.order_by('-created_at')
        
        context = {
            'received_offers': received_offers,
            'sent_offers': sent_offers,
            'show_all': show_all,
        }
        return render(request, self.template_name, context)


class AcceptTradeOfferView(LoginRequiredMixin, View):
    """Accept a trade offer and enroll both users"""
    def post(self, request, offer_id):
        trade_offer = get_object_or_404(
            ClassTradeOffer,
            id=offer_id,
            receiver=request.user,
            status=ClassTradeOffer.PENDING
        )
        
        # Check if both classes are still available and tradeable
        if not trade_offer.requested_class.is_published or not trade_offer.requested_class.is_tradeable:
            messages.error(request, 'The requested class is no longer available for trading.')
            return HttpResponseRedirect(reverse('skills:trade_offers'))
        
        if not trade_offer.offered_class.is_published or not trade_offer.offered_class.is_tradeable:
            messages.error(request, 'The offered class is no longer available for trading.')
            return HttpResponseRedirect(reverse('skills:trade_offers'))
        
        # Check if either user is already enrolled
        if ClassEnrollment.objects.filter(
            user=trade_offer.proposer,
            teaching_class=trade_offer.requested_class,
            status=ClassEnrollment.ACTIVE
        ).exists():
            messages.warning(request, 'The proposer is already enrolled in the requested class.')
            trade_offer.status = ClassTradeOffer.CANCELLED
            trade_offer.decided_at = timezone.now()
            trade_offer.save()
            return HttpResponseRedirect(reverse('skills:trade_offers'))
        
        if ClassEnrollment.objects.filter(
            user=trade_offer.receiver,
            teaching_class=trade_offer.offered_class,
            status=ClassEnrollment.ACTIVE
        ).exists():
            messages.warning(request, 'You are already enrolled in the offered class.')
            trade_offer.status = ClassTradeOffer.CANCELLED
            trade_offer.decided_at = timezone.now()
            trade_offer.save()
            return HttpResponseRedirect(reverse('skills:trade_offers'))
        
        # Enroll both users
        ClassEnrollment.objects.update_or_create(
            user=trade_offer.proposer,
            teaching_class=trade_offer.requested_class,
            defaults={
                'status': ClassEnrollment.ACTIVE,
                'granted_via': ClassEnrollment.TRADE,
                'purchase_id': f'trade_{trade_offer.id}'
            }
        )
        
        ClassEnrollment.objects.update_or_create(
            user=trade_offer.receiver,
            teaching_class=trade_offer.offered_class,
            defaults={
                'status': ClassEnrollment.ACTIVE,
                'granted_via': ClassEnrollment.TRADE,
                'purchase_id': f'trade_{trade_offer.id}'
            }
        )
        
        # Update trade offer status
        trade_offer.status = ClassTradeOffer.ACCEPTED
        trade_offer.decided_at = timezone.now()
        trade_offer.save()
        
        # Create a message in the chat system
        conversation = get_or_create_conversation(request.user, trade_offer.proposer)
        message_content = f"Great news! I've accepted your trade offer. 🎉\n\nYou are now enrolled in '{trade_offer.requested_class.title}' and I'm enrolled in '{trade_offer.offered_class.title}'.\n\nLet's learn together!"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        messages.success(request, f'Trade accepted! You are now enrolled in "{trade_offer.offered_class.title}" and {trade_offer.proposer.username} is enrolled in "{trade_offer.requested_class.title}".')
        return HttpResponseRedirect(reverse('skills:trade_offers'))


class DeclineTradeOfferView(LoginRequiredMixin, View):
    """Decline a trade offer"""
    def post(self, request, offer_id):
        trade_offer = get_object_or_404(
            ClassTradeOffer,
            id=offer_id,
            receiver=request.user,
            status=ClassTradeOffer.PENDING
        )
        
        trade_offer.status = ClassTradeOffer.DECLINED
        trade_offer.decided_at = timezone.now()
        trade_offer.save()
        
        # Create a message in the chat system
        conversation = get_or_create_conversation(request.user, trade_offer.proposer)
        message_content = f"I've declined your trade offer for '{trade_offer.requested_class.title}'.\n\nThanks for your interest! Feel free to reach out if you have other trade proposals."
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        messages.info(request, 'Trade offer declined.')
        return HttpResponseRedirect(reverse('skills:trade_offers'))


class CancelTradeOfferView(LoginRequiredMixin, View):
    """Cancel a trade offer (by the proposer)"""
    def post(self, request, offer_id):
        trade_offer = get_object_or_404(
            ClassTradeOffer,
            id=offer_id,
            proposer=request.user,
            status=ClassTradeOffer.PENDING
        )
        
        trade_offer.status = ClassTradeOffer.CANCELLED
        trade_offer.decided_at = timezone.now()
        trade_offer.save()
        
        # Create a message in the chat system
        conversation = get_or_create_conversation(request.user, trade_offer.receiver)
        message_content = f"I've cancelled my trade offer for '{trade_offer.requested_class.title}'.\n\nSorry for any inconvenience. Feel free to reach out if you'd like to discuss other trade opportunities!"
        
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content
        )
        
        messages.info(request, 'Trade offer cancelled.')
        return HttpResponseRedirect(reverse('skills:trade_offers'))


class TeacherApplicationCreateView(LoginRequiredMixin, CreateView):
    model = TeacherApplication
    fields = [
        'title', 'bio', 'intro_video', 'thumbnail', 'difficulty', 'duration_minutes', 'is_tradeable', 'portfolio_links', 'expertise_topics'
    ]
    template_name = 'skills/teacher_apply.html'

    def dispatch(self, request, *args, **kwargs):
        """Check if user is verified before allowing class creation"""
        from users.models import Profile
        try:
            profile = Profile.objects.get(user=request.user)
            if profile.verification_status != 'verified':
                messages.error(request, 'You must verify your identity before creating a class. Please complete identity verification first.')
                return redirect('users:verify_identity')
        except Profile.DoesNotExist:
            messages.error(request, 'Profile not found. Please complete your profile setup first.')
            return redirect('users:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.applicant = self.request.user
        # Convert dollar input to cents if provided and normalize booleans
        price_dollars = self.request.POST.get('price_dollars')
        if price_dollars is not None and price_dollars != '':
            try:
                cents = int((Decimal(price_dollars) * 100).quantize(Decimal('1')))
                form.instance.price_cents = max(cents, 0)
            except (InvalidOperation, ValueError):
                form.instance.price_cents = 0
        # is_tradeable may come as 'true'/'false' from the select
        trade_val = self.request.POST.get('is_tradeable')
        if trade_val is not None:
            form.instance.is_tradeable = str(trade_val).lower() in ['true', '1', 'on', 'yes']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('skills:class_list')


class ClassEditView(LoginRequiredMixin, View):
    template_name = 'skills/class_edit.html'
    
    def get_object(self):
        obj = get_object_or_404(TeachingClass, slug=self.kwargs['slug'])
        # Check permissions: admin can edit all, users can only edit their own
        if not (self.request.user.is_staff or obj.teacher_id == self.request.user.id):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to edit this class.")
        return obj
    
    def get(self, request, slug):
        teaching_class = self.get_object()
        context = {
            'teaching_class': teaching_class,
            'price_dollars': teaching_class.price_cents / 100.0 if teaching_class.price_cents else 0,
            'is_admin': request.user.is_staff,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, slug):
        teaching_class = self.get_object()
        
        # If admin, update class directly
        if request.user.is_staff:
            return self._update_class_directly(request, teaching_class)
        else:
            # If regular user, create a new application for approval
            return self._create_edit_application(request, teaching_class)
    
    def _update_class_directly(self, request, teaching_class):
        """Admin can update class directly"""
        # Handle price conversion from dollars to cents
        price_dollars = request.POST.get('price_dollars')
        if price_dollars is not None and price_dollars != '':
            try:
                cents = int((Decimal(price_dollars) * 100).quantize(Decimal('1')))
                teaching_class.price_cents = max(cents, 0)
            except (InvalidOperation, ValueError):
                teaching_class.price_cents = 0
        
        # Update fields
        teaching_class.title = request.POST.get('title', teaching_class.title)
        teaching_class.short_description = request.POST.get('short_description', teaching_class.short_description)
        teaching_class.full_description = request.POST.get('full_description', teaching_class.full_description)
        teaching_class.difficulty = request.POST.get('difficulty', teaching_class.difficulty)
        
        try:
            teaching_class.duration_minutes = int(request.POST.get('duration_minutes', teaching_class.duration_minutes) or 0)
        except (ValueError, TypeError):
            teaching_class.duration_minutes = 0
        
        # Handle is_tradeable
        trade_val = request.POST.get('is_tradeable')
        teaching_class.is_tradeable = str(trade_val).lower() in ['true', '1', 'on', 'yes'] if trade_val else False
        
        teaching_class.trade_notes = request.POST.get('trade_notes', teaching_class.trade_notes)
        
        # Handle is_published checkbox
        published_val = request.POST.get('is_published')
        teaching_class.is_published = str(published_val).lower() in ['true', '1', 'on', 'yes'] if published_val else False
        
        # Handle file uploads
        if 'intro_video' in request.FILES:
            teaching_class.intro_video = request.FILES['intro_video']
        if 'thumbnail' in request.FILES:
            teaching_class.thumbnail = request.FILES['thumbnail']
        
        teaching_class.save()
        messages.success(request, 'Class updated successfully!')
        return HttpResponseRedirect(reverse('skills:class_detail', args=[teaching_class.slug]))
    
    def _create_edit_application(self, request, teaching_class):
        """Regular user creates an application for edit approval"""
        from django.utils.text import slugify
        
        # Handle price conversion from dollars to cents
        price_dollars = request.POST.get('price_dollars')
        price_cents = teaching_class.price_cents
        if price_dollars is not None and price_dollars != '':
            try:
                price_cents = int((Decimal(price_dollars) * 100).quantize(Decimal('1')))
                price_cents = max(price_cents, 0)
            except (InvalidOperation, ValueError):
                price_cents = teaching_class.price_cents
        
        # Handle duration
        try:
            duration_minutes = int(request.POST.get('duration_minutes', teaching_class.duration_minutes) or 0)
        except (ValueError, TypeError):
            duration_minutes = teaching_class.duration_minutes
        
        # Handle is_tradeable
        trade_val = request.POST.get('is_tradeable')
        is_tradeable = str(trade_val).lower() in ['true', '1', 'on', 'yes'] if trade_val else teaching_class.is_tradeable
        
        # Create new application for edit
        full_description = request.POST.get('full_description', teaching_class.full_description)
        short_description = request.POST.get('short_description', teaching_class.short_description)
        
        application = TeacherApplication.objects.create(
            applicant=request.user,
            title=request.POST.get('title', teaching_class.title),
            bio=full_description or short_description or teaching_class.full_description,
            difficulty=request.POST.get('difficulty', teaching_class.difficulty),
            duration_minutes=duration_minutes,
            price_cents=price_cents,
            is_tradeable=is_tradeable,
            status=TeacherApplication.PENDING,
        )
        
        # Handle file uploads - only if new files are provided
        if 'intro_video' in request.FILES:
            application.intro_video = request.FILES['intro_video']
            application.save()
        
        if 'thumbnail' in request.FILES:
            application.thumbnail = request.FILES['thumbnail']
            application.save()
        
        # Store reference to the class being edited in decision_notes for admin reference
        application.decision_notes = f"EDIT REQUEST for existing class: {teaching_class.slug} (ID: {teaching_class.id})"
        application.save()
        
        messages.success(request, 'Your class edit has been submitted for review. An admin will review your changes and update the class once approved.')
        return HttpResponseRedirect(reverse('skills:class_detail', args=[teaching_class.slug]))


class ClassDeleteView(LoginRequiredMixin, View):
    def post(self, request, slug):
        teaching_class = get_object_or_404(TeachingClass, slug=slug)
        if request.user.is_staff or teaching_class.teacher_id == request.user.id:
            teaching_class.delete()
            return HttpResponseRedirect(reverse('skills:class_list'))
        return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))


class ClassCheckoutView(LoginRequiredMixin, View):
    def post(self, request, slug):
        try:
            import stripe  # lazy import
        except Exception:
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]) + '?error=stripe_not_installed')

        cls = get_object_or_404(TeachingClass, slug=slug, is_published=True)
        # Check for active enrollment
        existing_enrollment = ClassEnrollment.objects.filter(
            user=request.user, 
            teaching_class=cls, 
            status=ClassEnrollment.ACTIVE
        ).first()
        
        if existing_enrollment:
            # Already enrolled and active - can't enroll again
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))
        
        # Check if there's a revoked enrollment (completed and unenrolled)
        revoked_enrollment = ClassEnrollment.objects.filter(
            user=request.user,
            teaching_class=cls,
            status=ClassEnrollment.REVOKED
        ).first()
        
        if revoked_enrollment:
            # Delete the old revoked enrollment to allow fresh re-enrollment
            revoked_enrollment.delete()
            messages.info(request, 'Welcome back! Starting fresh enrollment.')
        if (cls.price_cents or 0) <= 0:
            # Free enrollment disabled: require payment or trade
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]) + '?error=pricing_required')

        # Get time_slot_id from form data
        time_slot_id = request.POST.get('time_slot_id')
        booking_notes = request.POST.get('booking_notes', '').strip()
        
        # Validate time slot if provided
        if time_slot_id:
            try:
                time_slot = ClassTimeSlot.objects.get(id=time_slot_id, teaching_class=cls, is_active=True)
                if time_slot.start_time <= timezone.now():
                    messages.error(request, 'Selected time slot has passed. Please select another time.')
                    return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))
                if time_slot.is_fully_booked():
                    messages.error(request, 'Selected time slot is fully booked. Please select another time.')
                    return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))
            except ClassTimeSlot.DoesNotExist:
                messages.error(request, 'Invalid time slot selected.')
                return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))

        secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not secret:
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]) + '?error=stripe_not_configured')

        stripe.api_key = secret
        # Redirect to book a session page after successful payment
        success_url = request.build_absolute_uri(reverse('skills:view_schedule', args=[slug])) + '?paid=1&session_id={CHECKOUT_SESSION_ID}'
        cancel_url = request.build_absolute_uri(reverse('skills:class_detail', args=[slug])) + '?cancel=1'

        # Build metadata with booking info
        metadata = {
            'class_id': str(cls.id),
            'user_id': str(request.user.id),
        }
        if time_slot_id:
            metadata['time_slot_id'] = str(time_slot_id)
        if booking_notes:
            metadata['booking_notes'] = booking_notes[:500]  # Limit length

        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(cls.price_cents),
                    'product_data': {'name': cls.title},
                },
                'quantity': 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            payment_intent_data={
                'metadata': metadata,  # Also add metadata to payment intent for payment_intent events
            },
            customer_email=request.user.email if request.user.email else None,
        )
        return HttpResponseRedirect(session.url)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Comprehensive Stripe webhook handler for all payment events
    Handles: successful payments, failed payments, refunds, and cancellations
    """
    def get(self, request):
        """Test endpoint to verify webhook URL is accessible"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Webhook endpoint accessed via GET (test)")
        
        return JsonResponse({
            'status': 'ok',
            'message': 'Webhook endpoint is accessible',
            'webhook_secret_configured': bool(getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)),
            'stripe_secret_configured': bool(getattr(settings, 'STRIPE_SECRET_KEY', None)),
        })
    
    def post(self, request):
        import json
        import logging
        import traceback
        
        logger = logging.getLogger(__name__)
        
        # Log webhook attempt
        logger.info("=" * 60)
        logger.info("STRIPE WEBHOOK RECEIVED")
        logger.info(f"Method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Has STRIPE_WEBHOOK_SECRET: {bool(getattr(settings, 'STRIPE_WEBHOOK_SECRET', None))}")
        
        try:
            import stripe
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
            if not stripe.api_key:
                logger.error("STRIPE_SECRET_KEY not configured!")
                return HttpResponse(status=500)
        except ImportError:
            logger.error("Stripe library not installed")
            return HttpResponse(status=400)

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        
        logger.info(f"Payload length: {len(payload)} bytes")
        logger.info(f"Signature header present: {bool(sig_header)}")
        logger.info(f"Endpoint secret present: {bool(endpoint_secret)}")
        
        try:
            if endpoint_secret:
                logger.info("Verifying webhook signature...")
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
                logger.info("✓ Webhook signature verified successfully")
            else:
                logger.warning("⚠ No webhook secret configured - skipping signature verification (development mode)")
                # For development/testing without webhook secret
                event = stripe.Event.construct_from(json.loads(payload.decode('utf-8')), stripe.api_key)
        except ValueError as e:
            logger.error(f"❌ Invalid payload: {e}")
            logger.error(f"Payload preview: {payload[:200] if len(payload) > 0 else 'Empty'}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"❌ Invalid signature: {e}")
            logger.error(f"Expected secret: {endpoint_secret[:10]}..." if endpoint_secret else "No secret configured")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return HttpResponse(status=400)

        event_type = event['type']
        event_id = event.get('id', 'unknown')
        logger.info(f"✓ Received Stripe webhook: {event_type} (ID: {event_id})")

        # Handle checkout session completed (successful payment)
        if event_type == 'checkout.session.completed':
            logger.info("Processing checkout.session.completed event...")
            try:
                self._handle_checkout_completed(event)
                logger.info("✓ Successfully processed checkout.session.completed")
            except Exception as e:
                logger.error(f"❌ Error processing checkout.session.completed: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Handle payment intent succeeded (additional confirmation)
        elif event_type == 'payment_intent.succeeded':
            logger.info("Processing payment_intent.succeeded event...")
            self._handle_payment_succeeded(event)
        
        # Handle payment intent failed
        elif event_type == 'payment_intent.payment_failed':
            logger.info("Processing payment_intent.payment_failed event...")
            self._handle_payment_failed(event)
        
        # Handle refunds
        elif event_type == 'charge.refunded':
            logger.info("Processing charge.refunded event...")
            self._handle_refund(event)
        
        # Handle payment disputes
        elif event_type == 'charge.dispute.created':
            logger.info("Processing charge.dispute.created event...")
            self._handle_dispute(event)
        else:
            logger.info(f"Unhandled event type: {event_type}")

        logger.info("=" * 60)
        return HttpResponse(status=200)

    def _handle_checkout_completed(self, event):
        """Handle successful checkout session completion"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            session = event['data']['object']
            session_id = session.get('id', 'unknown')
            logger.info(f"Processing checkout session: {session_id}")
            
            metadata = session.get('metadata', {})
            logger.info(f"Session metadata: {metadata}")
            
            class_id = metadata.get('class_id')
            user_id = metadata.get('user_id')
            time_slot_id = metadata.get('time_slot_id')
            booking_notes = metadata.get('booking_notes', '')
            
            if not class_id or not user_id:
                logger.warning(f"❌ Missing metadata in checkout session: {session_id}")
                logger.warning(f"Metadata received: {metadata}")
                return
            
            logger.info(f"Processing enrollment - Class ID: {class_id}, User ID: {user_id}, Time Slot ID: {time_slot_id}")
            
            try:
                cls = TeachingClass.objects.get(id=class_id)
                user_id_int = int(user_id)
                
                # Delete any existing revoked enrollment first (for fresh re-enrollment)
                ClassEnrollment.objects.filter(
                    user_id=user_id_int,
                    teaching_class=cls,
                    status=ClassEnrollment.REVOKED
                ).delete()
                
                # Check if there's an existing active enrollment (shouldn't happen, but handle it)
                existing_active = ClassEnrollment.objects.filter(
                    user_id=user_id_int,
                    teaching_class=cls,
                    status=ClassEnrollment.ACTIVE
                ).first()
                
                if existing_active:
                    # Update existing active enrollment with new payment info
                    existing_active.granted_via = ClassEnrollment.PURCHASE
                    existing_active.purchase_id = session.get('payment_intent') or session.get('id')
                    existing_active.save()
                    enrollment = existing_active
                    created = False
                else:
                    # Create new enrollment (fresh start after revocation)
                    enrollment = ClassEnrollment.objects.create(
                        user_id=user_id_int,
                        teaching_class=cls,
                        status=ClassEnrollment.ACTIVE,
                        granted_via=ClassEnrollment.PURCHASE,
                        purchase_id=session.get('payment_intent') or session.get('id')
                    )
                    created = True
                
                if created:
                    logger.info(f"Created enrollment for user {user_id_int} in class {class_id}")
                else:
                    logger.info(f"Updated enrollment for user {user_id_int} in class {class_id}")
                
                # Create booking if time slot was specified during checkout
                if time_slot_id and enrollment:
                    self._create_booking_from_checkout(enrollment, user_id_int, time_slot_id, booking_notes, logger)
                        
            except TeachingClass.DoesNotExist:
                logger.error(f"Class {class_id} not found")
            except ValueError:
                logger.error(f"Invalid user_id: {user_id}")
            except Exception as e:
                logger.error(f"Error processing checkout completion: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error in _handle_checkout_completed: {e}")
    
    def _create_booking_from_checkout(self, enrollment, user_id, time_slot_id, booking_notes, logger):
        """Helper to create booking from checkout metadata with proper validation"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get user object
            user = User.objects.get(pk=user_id)
            
            time_slot = ClassTimeSlot.objects.get(
                id=time_slot_id, 
                teaching_class=enrollment.teaching_class
            )
            
            # Validate slot can be booked using model method
            can_book, error_msg = time_slot.can_be_booked_by(user)
            if not can_book:
                logger.warning(f"Cannot create booking for slot {time_slot_id}: {error_msg}")
                return
            
            # Check if there's an existing cancelled booking for this slot
            existing_booking = ClassBooking.objects.filter(
                time_slot=time_slot,
                student=user,
                status=ClassBooking.CANCELLED
            ).first()
            
            if existing_booking:
                # Reactivate the cancelled booking
                existing_booking.status = ClassBooking.CONFIRMED
                existing_booking.notes = booking_notes[:1000] if booking_notes else ''
                existing_booking.cancelled_at = None
                existing_booking.enrollment = enrollment
                existing_booking.save()
                booking = existing_booking
                created = False
                logger.info(f"Reactivated cancelled booking {booking.id} for enrollment {enrollment.id}")
            else:
                # Create new booking
                booking, created = ClassBooking.objects.get_or_create(
                    time_slot=time_slot,
                    student=user,
                    enrollment=enrollment,
                    defaults={
                        'status': ClassBooking.CONFIRMED,
                        'notes': booking_notes[:1000] if booking_notes else '',  # Limit length
                    }
                )
                
                if created:
                    logger.info(f"Created booking {booking.id} for enrollment {enrollment.id}")
                else:
                    logger.info(f"Booking already exists for slot {time_slot_id} and user {user_id}")
                
        except ClassTimeSlot.DoesNotExist:
            logger.warning(f"Time slot {time_slot_id} not found")
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
        except Exception as e:
            logger.error(f"Error creating booking from checkout: {e}", exc_info=True)

    def _handle_payment_succeeded(self, event):
        """Handle payment intent succeeded (additional confirmation)"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            payment_intent = event['data']['object']
            # Payment intent succeeded is usually handled by checkout.session.completed
            # This is just for additional logging/confirmation
            logger.info(f"Payment intent succeeded: {payment_intent.get('id')}")
        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")

    def _handle_payment_failed(self, event):
        """Handle failed payment attempts"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            payment_intent = event['data']['object']
            metadata = payment_intent.get('metadata', {})
            class_id = metadata.get('class_id')
            user_id = metadata.get('user_id')
            
            logger.warning(f"Payment failed for user {user_id}, class {class_id}: {payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')}")
            
            # Optionally update enrollment status to pending or create a failed payment record
            if class_id and user_id:
                try:
                    enrollment = ClassEnrollment.objects.filter(
                        user_id=int(user_id),
                        teaching_class_id=int(class_id),
                        purchase_id=payment_intent.get('id')
                    ).first()
                    if enrollment and enrollment.status == ClassEnrollment.PENDING:
                        # Keep as pending or mark for retry
                        logger.info(f"Payment failed, enrollment remains pending for user {user_id}")
                except Exception as e:
                    logger.error(f"Error handling failed payment: {e}")
        except Exception as e:
            logger.error(f"Error in _handle_payment_failed: {e}")

    def _handle_refund(self, event):
        """Handle refunds - update enrollment status"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            charge = event['data']['object']
            payment_intent_id = charge.get('payment_intent')
            
            if not payment_intent_id:
                return
            
            # Find enrollment by purchase_id
            enrollments = ClassEnrollment.objects.filter(
                purchase_id=payment_intent_id,
                status=ClassEnrollment.ACTIVE
            )
            
            for enrollment in enrollments:
                enrollment.status = ClassEnrollment.REFUNDED
                enrollment.save()
                
                # Cancel any associated bookings
                bookings = ClassBooking.objects.filter(
                    enrollment=enrollment,
                    status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING]
                )
                for booking in bookings:
                    booking.status = ClassBooking.CANCELLED
                    booking.save()
                
                logger.info(f"Refunded enrollment {enrollment.id} for user {enrollment.user_id}")
                
        except Exception as e:
            logger.error(f"Error handling refund: {e}")

    def _handle_dispute(self, event):
        """Handle payment disputes"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            dispute = event['data']['object']
            charge_id = dispute.get('charge')
            logger.warning(f"Payment dispute created for charge {charge_id}")
            # You may want to mark enrollment as disputed or notify admin
        except Exception as e:
            logger.error(f"Error handling dispute: {e}")


# ============ SCHEDULING VIEWS ============

@login_required
def manage_class_schedule(request, slug):
    """Teacher view to manage time slots for their class"""
    teaching_class = get_object_or_404(TeachingClass, slug=slug, teacher=request.user)
    
    # Get all time slots for this class
    time_slots = ClassTimeSlot.objects.filter(
        teaching_class=teaching_class
    ).prefetch_related('bookings').order_by('start_time')
    
    # Get upcoming and past slots
    now = timezone.now()
    upcoming_slots = time_slots.filter(start_time__gte=now)
    past_slots = time_slots.filter(start_time__lt=now)
    
    # Annotate slots with booking info
    for slot in upcoming_slots:
        slot.has_active_bookings = slot.bookings.filter(
            status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING]
        ).exists()
    
    context = {
        'teaching_class': teaching_class,
        'upcoming_slots': upcoming_slots,
        'past_slots': past_slots,
    }
    return render(request, 'skills/manage_schedule.html', context)


@login_required
@require_http_methods(["POST"])
def create_time_slot(request, slug):
    """Create a new time slot for a class"""
    teaching_class = get_object_or_404(TeachingClass, slug=slug, teacher=request.user)
    
    try:
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        max_students = int(request.POST.get('max_students', 1))
        notes = request.POST.get('notes', '')
        
        from django.utils.dateparse import parse_datetime
        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str)
        
        if not start_time or not end_time:
            messages.error(request, 'Invalid date/time format.')
            return redirect('skills:manage_schedule', slug=slug)
        
        if end_time <= start_time:
            messages.error(request, 'End time must be after start time.')
            return redirect('skills:manage_schedule', slug=slug)
        
        ClassTimeSlot.objects.create(
            teaching_class=teaching_class,
            start_time=start_time,
            end_time=end_time,
            max_students=max_students,
            notes=notes,
        )
        messages.success(request, 'Time slot created successfully!')
    except Exception as e:
        messages.error(request, f'Error creating time slot: {str(e)}')
    
    return redirect('skills:manage_schedule', slug=slug)


@login_required
@require_http_methods(["POST"])
def delete_time_slot(request, slot_id):
    """Delete a time slot"""
    time_slot = get_object_or_404(ClassTimeSlot, id=slot_id, teaching_class__teacher=request.user)
    
    # Check if there are any confirmed bookings
    if time_slot.bookings.filter(status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING]).exists():
        messages.error(request, 'Cannot delete time slot with existing bookings.')
        return redirect('skills:manage_schedule', slug=time_slot.teaching_class.slug)
    
    teaching_class_slug = time_slot.teaching_class.slug
    time_slot.delete()
    messages.success(request, 'Time slot deleted successfully!')
    return redirect('skills:manage_schedule', slug=teaching_class_slug)


@login_required
def get_available_slots(request, slug):
    """API endpoint to get available time slots for booking modal"""
    from django.http import JsonResponse
    from datetime import datetime
    
    teaching_class = get_object_or_404(TeachingClass, slug=slug, is_published=True)
    
    # Get available time slots (upcoming, active, not fully booked)
    now = timezone.now()
    available_slots = ClassTimeSlot.objects.filter(
        teaching_class=teaching_class,
        is_active=True,
        start_time__gte=now
    ).prefetch_related('bookings').order_by('start_time')
    
    # Filter out fully booked slots
    available_slots = [slot for slot in available_slots if not slot.is_fully_booked()]
    
    # Group slots by date
    slots_by_date = {}
    for slot in available_slots:
        date_key = slot.start_time.date().isoformat()
        if date_key not in slots_by_date:
            slots_by_date[date_key] = []
        slots_by_date[date_key].append({
            'id': slot.id,
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
            'start_time_display': slot.start_time.strftime('%I:%M %p'),
            'end_time_display': slot.end_time.strftime('%I:%M %p'),
            'date_display': slot.start_time.strftime('%a, %d %b'),
            'available_spots': slot.get_available_spots(),
            'max_students': slot.max_students,
        })
    
    return JsonResponse({
        'slots_by_date': slots_by_date,
        'dates': sorted(slots_by_date.keys()),
    })


@login_required
def view_class_schedule(request, slug):
    """Student view to see available time slots and book them"""
    teaching_class = get_object_or_404(TeachingClass, slug=slug, is_published=True)
    
    # Handle payment success - verify enrollment if webhook didn't fire
    if request.GET.get('paid') == '1':
        session_id = request.GET.get('session_id')
        session_key = f'payment_processed_{session_id}' if session_id else f'payment_processed_{teaching_class.id}'
        
        # Only process if we haven't shown the message for this payment yet
        if not request.session.get(session_key):
            # Delete any revoked enrollments first (for re-enrollment)
            ClassEnrollment.objects.filter(
                user=request.user,
                teaching_class=teaching_class,
                status=ClassEnrollment.REVOKED
            ).delete()
            
            # Try to verify and create enrollment if webhook didn't fire
            enrollment = ClassEnrollment.objects.filter(
                user=request.user,
                teaching_class=teaching_class,
                status=ClassEnrollment.ACTIVE
            ).first()
            
            if not enrollment:
                try:
                    import stripe
                    secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
                    if secret:
                        stripe.api_key = secret
                        if session_id:
                            try:
                                session = stripe.checkout.Session.retrieve(session_id)
                                metadata = session.get('metadata', {})
                                if (session.get('payment_status') == 'paid' and 
                                    metadata.get('class_id') == str(teaching_class.id) and
                                    metadata.get('user_id') == str(request.user.id)):
                                    # Create enrollment from session
                                    from skills.views import ClassDetailView
                                    detail_view = ClassDetailView()
                                    detail_view.request = request
                                    detail_view._create_enrollment_from_session(request.user, teaching_class, session, metadata)
                                    # Refresh enrollment check
                                    enrollment = ClassEnrollment.objects.filter(
                                        user=request.user,
                                        teaching_class=teaching_class,
                                        status=ClassEnrollment.ACTIVE
                                    ).first()
                            except Exception as e:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.error(f"Error verifying payment in view_schedule: {e}")
                except Exception:
                    pass
            
            if enrollment:
                messages.success(request, f'Payment successful! You are now enrolled in "{teaching_class.title}". You can now book your sessions.')
                # Mark as processed to prevent duplicate messages
                request.session[session_key] = True
            else:
                messages.warning(request, 'Payment received! Your enrollment is being processed. Please wait a moment and refresh the page.')
                return redirect('skills:class_detail', slug=slug)
        
        # Redirect to clean URL without parameters to prevent message on refresh
        if request.GET.get('paid') == '1':
            return redirect('skills:view_schedule', slug=slug)
    
    # Check if user is enrolled - must be ACTIVE (not REVOKED)
    enrollment = ClassEnrollment.objects.filter(
        user=request.user,
        teaching_class=teaching_class,
        status=ClassEnrollment.ACTIVE
    ).first()
    
    if not enrollment:
        # Check if there's a revoked enrollment
        revoked_enrollment = ClassEnrollment.objects.filter(
            user=request.user,
            teaching_class=teaching_class,
            status=ClassEnrollment.REVOKED
        ).first()
        
        if revoked_enrollment:
            messages.info(request, 'You have completed this class. Please re-enroll through payment to book new sessions.')
        else:
            messages.error(request, 'You must be enrolled in this class to book sessions.')
        return redirect('skills:class_detail', slug=slug)
    
    # Get available time slots (upcoming, active, not fully booked)
    now = timezone.now()
    available_slots = ClassTimeSlot.objects.filter(
        teaching_class=teaching_class,
        is_active=True,
        start_time__gte=now
    ).prefetch_related('bookings').order_by('start_time')
    
    # Filter out fully booked slots
    available_slots = [slot for slot in available_slots if not slot.is_fully_booked()]
    
    # Get user's existing bookings for this class - separate active and completed
    all_user_bookings = ClassBooking.objects.filter(
        student=request.user,
        time_slot__teaching_class=teaching_class
    ).select_related('time_slot').order_by('-time_slot__start_time')  # Most recent first
    
    # Separate bookings into active and completed using model methods
    user_bookings = [b for b in all_user_bookings if b.is_active() or (b.is_completed() and not b.is_student_confirmed())]
    completed_bookings = [b for b in all_user_bookings if b.is_completed() and b.is_student_confirmed()]
    
    # Sort them
    user_bookings = sorted(user_bookings, key=lambda b: b.time_slot.start_time)
    completed_bookings = sorted(completed_bookings, key=lambda b: b.time_slot.start_time, reverse=True)
    
    # Check and revoke enrollment if all sessions are completed
    enrollment.check_and_revoke_if_complete()
    enrollment.refresh_from_db()
    is_completed = enrollment.status == ClassEnrollment.REVOKED
    
    context = {
        'teaching_class': teaching_class,
        'enrollment': enrollment,
        'is_enrolled': True,  # User is enrolled if they reached this view
        'is_completed': is_completed,
        'available_slots': available_slots,
        'user_bookings': user_bookings,
        'completed_bookings': completed_bookings,
        'now': now,  # Pass current time to template
    }
    return render(request, 'skills/view_schedule.html', context)


@login_required
@require_http_methods(["POST"])
def book_time_slot(request, slot_id):
    """Book a time slot with proper validation"""
    time_slot = get_object_or_404(ClassTimeSlot, id=slot_id, is_active=True)
    
    # Get active enrollment
    enrollment = ClassEnrollment.objects.filter(
        user=request.user,
        teaching_class=time_slot.teaching_class,
        status=ClassEnrollment.ACTIVE
    ).first()
    
    # Validate enrollment
    if not enrollment:
        revoked_enrollment = ClassEnrollment.objects.filter(
            user=request.user,
            teaching_class=time_slot.teaching_class,
            status=ClassEnrollment.REVOKED
        ).first()
        
        if revoked_enrollment:
            messages.info(request, 'You have completed this class. Please re-enroll through payment to book new sessions.')
        else:
            messages.error(request, 'You must be enrolled in this class to book sessions.')
        return redirect('skills:class_detail', slug=time_slot.teaching_class.slug)
    
    # Check if enrollment can book sessions
    if not enrollment.can_book_sessions():
        enrollment.check_and_revoke_if_complete()
        messages.info(request, 'You have completed this class. Please re-enroll through payment to book new sessions.')
        return redirect('skills:class_detail', slug=time_slot.teaching_class.slug)
    
    # Validate slot can be booked using model method
    can_book, error_msg = time_slot.can_be_booked_by(request.user)
    if not can_book:
        messages.error(request, error_msg or 'This time slot cannot be booked.')
        return redirect('skills:view_schedule', slug=time_slot.teaching_class.slug)
    
    # Check if there's an existing cancelled booking for this slot
    existing_booking = ClassBooking.objects.filter(
        time_slot=time_slot,
        student=request.user,
        status=ClassBooking.CANCELLED
    ).first()
    
    notes = request.POST.get('notes', '').strip()[:1000]  # Limit length
    
    if existing_booking:
        # Reactivate the cancelled booking
        existing_booking.status = ClassBooking.CONFIRMED
        existing_booking.notes = notes
        existing_booking.cancelled_at = None
        existing_booking.enrollment = enrollment  # Update enrollment in case it changed
        existing_booking.save()
        booking = existing_booking
        messages.success(request, f'Successfully re-booked session for {time_slot.start_time.strftime("%B %d, %Y at %I:%M %p")}!')
    else:
        # Create new booking
        booking = ClassBooking.objects.create(
            time_slot=time_slot,
            student=request.user,
            enrollment=enrollment,
            notes=notes,
            status=ClassBooking.CONFIRMED,
        )
        messages.success(request, f'Successfully booked session for {time_slot.start_time.strftime("%B %d, %Y at %I:%M %p")}!')
    
    return redirect('skills:view_schedule', slug=time_slot.teaching_class.slug)


@login_required
@require_http_methods(["POST"])
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(ClassBooking, id=booking_id, student=request.user)
    
    if not booking.can_be_cancelled():
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('skills:view_schedule', slug=booking.time_slot.teaching_class.slug)
    
    booking.status = ClassBooking.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save()
    
    messages.success(request, 'Booking cancelled successfully.')
    return redirect('skills:view_schedule', slug=booking.time_slot.teaching_class.slug)


@login_required
def my_bookings(request):
    """View all user's bookings across all classes"""
    bookings = ClassBooking.objects.filter(
        student=request.user
    ).select_related('time_slot', 'time_slot__teaching_class', 'enrollment').order_by('time_slot__start_time')
    
    # Separate by status
    upcoming = bookings.filter(
        time_slot__start_time__gte=timezone.now(),
        status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING]
    )
    past = bookings.filter(
        time_slot__start_time__lt=timezone.now()
    ) | bookings.filter(status=ClassBooking.COMPLETED)
    cancelled = bookings.filter(status=ClassBooking.CANCELLED)
    
    context = {
        'upcoming_bookings': upcoming,
        'past_bookings': past,
        'cancelled_bookings': cancelled,
    }
    return render(request, 'skills/my_bookings.html', context)


@login_required
def toggle_favorite(request, slug):
    """Toggle favorite status for a class"""
    teaching_class = get_object_or_404(TeachingClass, slug=slug, is_published=True)
    favorite, created = ClassFavorite.objects.get_or_create(
        user=request.user,
        teaching_class=teaching_class
    )
    if not created:
        favorite.delete()
        is_favorited = False
    else:
        is_favorited = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorited': is_favorited})
    return redirect('skills:class_detail', slug=slug)


@login_required
def my_favorites(request):
    """View user's favorite classes"""
    favorites = ClassFavorite.objects.filter(
        user=request.user
    ).select_related('teaching_class', 'teaching_class__teacher').prefetch_related('teaching_class__topics')
    
    classes = [fav.teaching_class for fav in favorites]
    
    context = {
        'classes': classes,
    }
    return render(request, 'skills/my_favorites.html', context)


# ============ COMPLETION VIEWS ============

@login_required
@require_http_methods(["POST"])
def complete_booking(request, booking_id):
    """Teacher marks a booking/session as completed"""
    booking = get_object_or_404(ClassBooking, id=booking_id)
    teaching_class = booking.time_slot.teaching_class
    
    # Check if user is the teacher
    if teaching_class.teacher != request.user and not request.user.is_staff:
        messages.error(request, 'Only the teacher can mark sessions as completed.')
        return redirect('skills:manage_schedule', slug=teaching_class.slug)
    
    # Validate booking can be marked complete
    if not booking.can_be_marked_complete():
        if booking.is_completed():
            messages.info(request, 'This session is already marked as completed.')
        else:
            messages.error(request, 'This session cannot be marked as completed yet.')
        return redirect('skills:manage_schedule', slug=teaching_class.slug)
    
    # Mark as completed
    booking.status = ClassBooking.COMPLETED
    booking.save()
    
    # Check if student has already confirmed
    enrollment = booking.enrollment
    if booking.is_student_confirmed():
        # Both teacher and student confirmed - check if enrollment should be revoked
        if enrollment.check_and_revoke_if_complete():
            messages.success(request, f'Session completed and confirmed! {booking.student.username} has been unenrolled. They can re-enroll anytime.')
        else:
            messages.success(request, f'Session marked as completed. Waiting for student confirmation on remaining sessions.')
    else:
        messages.success(request, f'Session marked as completed. Waiting for student confirmation.')
    
    return redirect('skills:manage_schedule', slug=teaching_class.slug)


@login_required
@require_http_methods(["POST"])
def confirm_booking_completion(request, booking_id):
    """Student confirms that a session was completed"""
    booking = get_object_or_404(ClassBooking, id=booking_id, student=request.user)
    teaching_class = booking.time_slot.teaching_class
    enrollment = booking.enrollment
    
    # Validate student can confirm
    if not booking.can_be_confirmed_by_student():
        if booking.is_student_confirmed():
            messages.info(request, 'You have already confirmed this session.')
        else:
            messages.error(request, 'This session cannot be confirmed yet.')
        return redirect('skills:view_schedule', slug=teaching_class.slug)
    
    # Mark student confirmation
    booking.mark_student_confirmed()
    
    # Check if teacher has also marked it as completed
    if booking.is_completed():
        # Both teacher and student confirmed - check if enrollment should be revoked
        if enrollment.check_and_revoke_if_complete():
            messages.success(request, f'Thank you for confirming! You have completed all sessions for "{teaching_class.title}". You have been unenrolled and can re-enroll anytime for a fresh start.')
        else:
            messages.success(request, 'Thank you for confirming! Your session completion has been recorded.')
    else:
        # Student confirmed but teacher hasn't marked it complete yet
        messages.success(request, 'Your confirmation has been recorded. Waiting for teacher to mark the session as completed.')
    
    return redirect('skills:view_schedule', slug=teaching_class.slug)



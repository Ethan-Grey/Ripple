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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cls = self.object
        is_enrolled = False
        is_favorited = False
        if user.is_authenticated:
            is_enrolled = ClassEnrollment.objects.filter(user=user, teaching_class=cls, status=ClassEnrollment.ACTIVE).exists()
            is_favorited = ClassFavorite.objects.filter(user=user, teaching_class=cls).exists()
        context['is_enrolled'] = is_enrolled
        context['is_favorited'] = is_favorited
        return context


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
        if ClassEnrollment.objects.filter(user=request.user, teaching_class=cls, status=ClassEnrollment.ACTIVE).exists():
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]))
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
        success_url = request.build_absolute_uri(reverse('skills:class_detail', args=[slug])) + '?paid=1'
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
            customer_email=request.user.email if request.user.email else None,
        )
        return HttpResponseRedirect(session.url)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request):
        try:
            import stripe
        except Exception:
            return HttpResponse(status=400)

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        try:
            if endpoint_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            else:
                event = stripe.Event.construct_from(json.loads(payload.decode('utf-8')), stripe.api_key)
        except Exception:
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            metadata = session.get('metadata', {})
            class_id = metadata.get('class_id')
            user_id = metadata.get('user_id')
            time_slot_id = metadata.get('time_slot_id')
            booking_notes = metadata.get('booking_notes', '')
            
            if class_id and user_id:
                try:
                    cls = TeachingClass.objects.get(id=class_id)
                    user_id_int = int(user_id)
                    
                    # Create enrollment
                    enrollment, created = ClassEnrollment.objects.update_or_create(
                        user_id=user_id_int,
                        teaching_class=cls,
                        defaults={
                            'status': ClassEnrollment.ACTIVE,
                            'granted_via': ClassEnrollment.PURCHASE,
                            'purchase_id': session.get('payment_intent') or session.get('id')
                        },
                    )
                    
                    # Create booking if time_slot_id was provided
                    if time_slot_id and enrollment:
                        try:
                            time_slot = ClassTimeSlot.objects.get(id=time_slot_id, teaching_class=cls)
                            # Double-check slot is still available
                            if not time_slot.is_fully_booked() and time_slot.start_time > timezone.now():
                                ClassBooking.objects.create(
                                    time_slot=time_slot,
                                    student_id=user_id_int,
                                    enrollment=enrollment,
                                    status=ClassBooking.CONFIRMED,
                                    notes=booking_notes,
                                )
                        except (ClassTimeSlot.DoesNotExist, Exception) as e:
                            # Log error but don't fail the enrollment
                            pass
                except Exception:
                    pass
        return HttpResponse(status=200)


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
    
    # Check if user is enrolled
    enrollment = ClassEnrollment.objects.filter(
        user=request.user,
        teaching_class=teaching_class,
        status=ClassEnrollment.ACTIVE
    ).first()
    
    if not enrollment:
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
    
    # Get user's existing bookings for this class
    user_bookings = ClassBooking.objects.filter(
        student=request.user,
        time_slot__teaching_class=teaching_class
    ).select_related('time_slot').order_by('time_slot__start_time')
    
    context = {
        'teaching_class': teaching_class,
        'enrollment': enrollment,
        'available_slots': available_slots,
        'user_bookings': user_bookings,
    }
    return render(request, 'skills/view_schedule.html', context)


@login_required
@require_http_methods(["POST"])
def book_time_slot(request, slot_id):
    """Book a time slot"""
    time_slot = get_object_or_404(ClassTimeSlot, id=slot_id, is_active=True)
    
    # Check if user is enrolled
    enrollment = ClassEnrollment.objects.filter(
        user=request.user,
        teaching_class=time_slot.teaching_class,
        status=ClassEnrollment.ACTIVE
    ).first()
    
    if not enrollment:
        messages.error(request, 'You must be enrolled in this class to book sessions.')
        return redirect('skills:class_detail', slug=time_slot.teaching_class.slug)
    
    # Check if slot is available
    if time_slot.is_fully_booked():
        messages.error(request, 'This time slot is fully booked.')
        return redirect('skills:view_schedule', slug=time_slot.teaching_class.slug)
    
    # Check if user already has a booking for this slot
    if ClassBooking.objects.filter(time_slot=time_slot, student=request.user).exists():
        messages.error(request, 'You already have a booking for this time slot.')
        return redirect('skills:view_schedule', slug=time_slot.teaching_class.slug)
    
    # Check if slot is in the past
    if time_slot.start_time <= timezone.now():
        messages.error(request, 'Cannot book a time slot in the past.')
        return redirect('skills:view_schedule', slug=time_slot.teaching_class.slug)
    
    # Create booking
    notes = request.POST.get('notes', '')
    ClassBooking.objects.create(
        time_slot=time_slot,
        student=request.user,
        enrollment=enrollment,
        notes=notes,
        status=ClassBooking.CONFIRMED,  # Auto-confirm for now
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



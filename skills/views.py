from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages

from .models import TeachingClass, ClassTopic, ClassReview, ClassEnrollment, ClassTradeOffer, TeacherApplication
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
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs


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
        if user.is_authenticated:
            is_enrolled = ClassEnrollment.objects.filter(user=user, teaching_class=cls, status=ClassEnrollment.ACTIVE).exists()
        context['is_enrolled'] = is_enrolled
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

        secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not secret:
            return HttpResponseRedirect(reverse('skills:class_detail', args=[slug]) + '?error=stripe_not_configured')

        stripe.api_key = secret
        success_url = request.build_absolute_uri(reverse('skills:class_detail', args=[slug])) + '?paid=1'
        cancel_url = request.build_absolute_uri(reverse('skills:class_detail', args=[slug])) + '?cancel=1'

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
            metadata={'class_id': str(cls.id), 'user_id': str(request.user.id)},
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
            class_id = session.get('metadata', {}).get('class_id')
            user_id = session.get('metadata', {}).get('user_id')
            if class_id and user_id:
                try:
                    cls = TeachingClass.objects.get(id=class_id)
                    user_id_int = int(user_id)
                    ClassEnrollment.objects.update_or_create(
                        user_id=user_id_int,
                        teaching_class=cls,
                        defaults={
                            'status': ClassEnrollment.ACTIVE,
                            'granted_via': ClassEnrollment.PURCHASE,
                            'purchase_id': session.get('payment_intent') or session.get('id')
                        },
                    )
                except Exception:
                    pass
        return HttpResponse(status=200)



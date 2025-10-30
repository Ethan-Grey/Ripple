from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.conf import settings

from .models import TeachingClass, ClassTopic, ClassReview, ClassEnrollment, ClassTradeOffer, TeacherApplication
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
            return HttpResponseRedirect(reverse('skills:class_detail', args=[requested_class.slug]))
        offered_class = get_object_or_404(TeachingClass, pk=offered_id, teacher=request.user)
        ClassTradeOffer.objects.create(
            proposer=request.user,
            receiver=requested_class.teacher,
            offered_class=offered_class,
            requested_class=requested_class,
            message=message,
        )
        return HttpResponseRedirect(reverse('skills:class_detail', args=[requested_class.slug]))


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



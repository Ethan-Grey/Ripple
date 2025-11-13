from django.db import models
from django.conf import settings
from django.utils import timezone


class Skill(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class UserSkill(models.Model):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'
    LEVEL_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
        (EXPERT, 'Expert'),
    ]

    UNVERIFIED = 'unverified'
    PENDING = 'pending'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    VERIFICATION_CHOICES = [
        (UNVERIFIED, 'Unverified'),
        (PENDING, 'Pending Review'),
        (VERIFIED, 'Verified'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    can_teach = models.BooleanField(default=False)
    wants_to_learn = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default=UNVERIFIED)
    verification_message = models.TextField(blank=True, help_text="Message from admin about verification status")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'skill')

    def __str__(self) -> str:
        return f"{self.user.username} - {self.skill.name} ({self.level})"


class SkillEvidence(models.Model):
    DOCUMENT = 'document'
    VIDEO = 'video'
    IMAGE = 'image'
    LINK = 'link'
    EVIDENCE_TYPE_CHOICES = [
        (DOCUMENT, 'Document'),
        (VIDEO, 'Video'),
        (IMAGE, 'Image'),
        (LINK, 'Link'),
    ]

    user_skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE, related_name='evidence')
    title = models.CharField(max_length=200, help_text="Title or description of the evidence")
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPE_CHOICES, default=DOCUMENT)
    file = models.FileField(upload_to='skill_evidence/', blank=True, null=True, help_text="Upload a file (document, video, image)")
    link = models.URLField(blank=True, help_text="Or provide a link to your work/portfolio")
    description = models.TextField(blank=True, help_text="Describe what this evidence demonstrates")
    created_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False, help_text="Mark as primary evidence for this skill")

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self) -> str:
        return f"{self.user_skill.skill.name} - {self.title}"


class Offer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers')
    teach_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='teach_offers')
    learn_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='learn_offers', null=True, blank=True)
    cash_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        label = f"Teach {self.teach_skill.name}"
        if self.learn_skill:
            label += f" ↔ Learn {self.learn_skill.name}"
        if self.cash_price is not None:
            label += f" (${self.cash_price})"
        return f"{self.user.username}: {label}"


class Match(models.Model):
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_a')
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_b')
    teach_a_learn_b = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='teach_a_learn_b')
    teach_b_learn_a = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='teach_b_learn_a')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_a', 'user_b', 'teach_a_learn_b', 'teach_b_learn_a')

    def __str__(self) -> str:
        return f"{self.user_a.username} ↔ {self.user_b.username}"

class SwipeAction(models.Model):
    """Track user swipe actions on classes"""
    SWIPE_RIGHT = 'right'  # Whitelist
    SWIPE_LEFT = 'left'    # Blacklist
    
    SWIPE_CHOICES = [
        (SWIPE_RIGHT, 'Interested'),
        (SWIPE_LEFT, 'Not Interested'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swipe_actions'
    )
    teaching_class = models.ForeignKey(
        'TeachingClass',
        on_delete=models.CASCADE,
        related_name='swipe_actions'
    )
    action = models.CharField(
        max_length=10,
        choices=SWIPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'teaching_class']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.teaching_class.title} - {self.action}"


class TeacherApplication(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    DIFFICULTY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    intro_video = models.FileField(upload_to='teacher_applications/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='teacher_applications/', blank=True, null=True)
    portfolio_links = models.TextField(blank=True, help_text='Comma or newline separated links')
    expertise_topics = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    duration_minutes = models.PositiveIntegerField(default=0)
    price_cents = models.PositiveIntegerField(default=0)
    is_tradeable = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    decision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_applications')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='reviewed_teacher_applications')
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def price_dollars(self):
        """Return price in dollars as a float"""
        return self.price_cents / 100.0
    
    def __str__(self):
        return f"{self.applicant.username} - {self.title} ({self.status})"


class TeachingClass(models.Model):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    DIFFICULTY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=300, blank=True)
    full_description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    duration_minutes = models.PositiveIntegerField(default=0)
    price_cents = models.PositiveIntegerField(default=0, help_text='Price in cents (e.g., 1999 = $19.99)')
    is_tradeable = models.BooleanField(default=False)
    trade_notes = models.CharField(max_length=200, blank=True)
    intro_video = models.FileField(upload_to='class_intros/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='class_thumbs/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teaching_classes')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ClassTopic(models.Model):
    name = models.CharField(max_length=80)
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='topics')
    
    def __str__(self):
        return f"{self.teaching_class.title} - {self.name}"


class ClassReview(models.Model):
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_reviews')
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='reviews')
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('teaching_class', 'reviewer')
    
    def __str__(self):
        return f"{self.reviewer.username} - {self.teaching_class.title} ({self.rating})"


class ClassEnrollment(models.Model):
    PENDING = 'pending'
    ACTIVE = 'active'
    REFUNDED = 'refunded'
    REVOKED = 'revoked'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACTIVE, 'Active'),
        (REFUNDED, 'Refunded'),
        (REVOKED, 'Revoked'),
    ]
    
    PURCHASE = 'purchase'
    TRADE = 'trade'
    GRANTED_VIA_CHOICES = [
        (PURCHASE, 'Purchase'),
        (TRADE, 'Trade'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    granted_via = models.CharField(max_length=20, choices=GRANTED_VIA_CHOICES)
    purchase_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_enrollments')
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='enrollments')
    
    class Meta:
        unique_together = ('user', 'teaching_class')
    
    def __str__(self):
        return f"{self.user.username} - {self.teaching_class.title} ({self.status})"


class ClassTradeOffer(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
        (CANCELLED, 'Cancelled'),
    ]
    
    message = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    expires_at = models.DateTimeField(blank=True, null=True)
    decided_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposed_class_trades')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_class_trades')
    offered_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='offers_made')
    requested_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='offers_received')
    
    def __str__(self):
        return f"{self.proposer.username} → {self.receiver.username}: {self.offered_class.title} ↔ {self.requested_class.title} ({self.status})"


class ClassTimeSlot(models.Model):
    """Available time slots that teachers can create for their classes"""
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField(help_text='When this time slot starts')
    end_time = models.DateTimeField(help_text='When this time slot ends')
    max_students = models.PositiveIntegerField(default=1, help_text='Maximum number of students for this slot')
    is_recurring = models.BooleanField(default=False, help_text='Is this a recurring slot?')
    recurrence_pattern = models.CharField(
        max_length=50, 
        blank=True, 
        help_text='e.g., "weekly", "daily", "MWF" for recurring slots'
    )
    notes = models.TextField(blank=True, help_text='Additional notes about this time slot')
    is_active = models.BooleanField(default=True, help_text='Is this slot currently available?')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['teaching_class', 'start_time']),
            models.Index(fields=['start_time', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.teaching_class.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def get_available_spots(self):
        """Get number of available spots remaining"""
        booked_count = self.bookings.filter(status__in=[ClassBooking.CONFIRMED, ClassBooking.PENDING]).count()
        return max(0, self.max_students - booked_count)
    
    def is_fully_booked(self):
        """Check if this slot is fully booked"""
        return self.get_available_spots() == 0


class ClassBooking(models.Model):
    """Bookings made by students for class time slots"""
    CONFIRMED = 'confirmed'
    PENDING = 'pending'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'
    STATUS_CHOICES = [
        (CONFIRMED, 'Confirmed'),
        (PENDING, 'Pending'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
        (NO_SHOW, 'No Show'),
    ]
    
    time_slot = models.ForeignKey(ClassTimeSlot, on_delete=models.CASCADE, related_name='bookings')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_bookings')
    enrollment = models.ForeignKey(
        ClassEnrollment, 
        on_delete=models.CASCADE, 
        related_name='bookings',
        help_text='The enrollment that grants access to this booking'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    notes = models.TextField(blank=True, help_text='Student notes or special requests')
    teacher_notes = models.TextField(blank=True, help_text='Teacher notes (private)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['time_slot__start_time']
        unique_together = ('time_slot', 'student')
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['time_slot', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.time_slot.teaching_class.title} - {self.time_slot.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def can_be_cancelled(self):
        """Check if booking can be cancelled"""
        return self.status in [ClassBooking.CONFIRMED, ClassBooking.PENDING] and self.time_slot.start_time > timezone.now()
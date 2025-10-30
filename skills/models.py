from django.db import models
from django.conf import settings


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


# Teaching classes domain
class TeachingClass(models.Model):
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    DIFFICULTY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
    ]

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teaching_classes')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    short_description = models.CharField(max_length=300, blank=True)
    full_description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    duration_minutes = models.PositiveIntegerField(default=0)
    price_cents = models.PositiveIntegerField(default=0, help_text="Price in cents (e.g., 1999 = $19.99)")
    is_tradeable = models.BooleanField(default=False)
    trade_notes = models.CharField(max_length=200, blank=True)
    intro_video = models.FileField(upload_to='class_intros/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='class_thumbs/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} by {self.teacher.username}"

    @property
    def price_display(self) -> str:
        dollars = (self.price_cents or 0) / 100
        return f"${dollars:0.2f}"


class ClassTopic(models.Model):
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=80)

    def __str__(self) -> str:
        return self.name


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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_enrollments')
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    granted_via = models.CharField(max_length=20, choices=GRANTED_VIA_CHOICES)
    purchase_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'teaching_class')

    def __str__(self) -> str:
        return f"{self.user.username} → {self.teaching_class.title} ({self.status})"


class ClassReview(models.Model):
    teaching_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('teaching_class', 'reviewer')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.rating}/5 by {self.reviewer.username}"


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

    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposed_class_trades')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_class_trades')
    offered_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='offers_made')
    requested_class = models.ForeignKey(TeachingClass, on_delete=models.CASCADE, related_name='offers_received')
    message = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    expires_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Trade {self.proposer.username} ↔ {self.receiver.username} ({self.status})"


class TeacherApplication(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_applications')
    title = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    intro_video = models.FileField(upload_to='teacher_applications/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='teacher_applications/', blank=True, null=True)
    # Desired class settings provided by the applicant
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    DIFFICULTY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=BEGINNER)
    duration_minutes = models.PositiveIntegerField(default=0)
    price_cents = models.PositiveIntegerField(default=0)
    is_tradeable = models.BooleanField(default=False)
    portfolio_links = models.TextField(blank=True, help_text="Comma or newline separated links")
    expertise_topics = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_teacher_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Application by {self.applicant.username} ({self.status})"

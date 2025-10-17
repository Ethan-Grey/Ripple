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

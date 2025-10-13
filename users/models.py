from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    verification_status = models.CharField(max_length=20, default='unverified')  # unverified|pending|verified

    def __str__(self) -> str:
        return f"Profile({self.user.username})"


class Evidence(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='evidence')
    title = models.CharField(max_length=140)
    file = models.FileField(upload_to='evidence/', blank=True, null=True)
    link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Evidence({self.title})"


class IdentitySubmission(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='identity_submissions')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    dob = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=120, blank=True)
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=120, blank=True)
    postal = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"IdentitySubmission({self.profile.user.username} @ {self.created_at:%Y-%m-%d})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    # Ensure profile stays in sync
    if hasattr(instance, 'profile'):
        instance.profile.save()

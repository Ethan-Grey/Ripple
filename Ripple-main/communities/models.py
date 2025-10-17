from django.db import models
from django.conf import settings
from skills.models import Skill


class Community(models.Model):
    name = models.CharField(max_length=140)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities', blank=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.skill.name})"

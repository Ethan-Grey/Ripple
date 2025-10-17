from django.contrib import admin
from .models import Profile, Evidence


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "verification_status")
    list_filter = ("verification_status",)
    search_fields = ("user__username", "location")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("profile", "title", "created_at")
    search_fields = ("title", "profile__user__username")

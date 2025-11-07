from django.contrib import admin
from .models import Skill, SwipeAction, UserSkill, Offer, Match


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill", "level", "can_teach", "wants_to_learn")
    list_filter = ("level", "can_teach", "wants_to_learn")
    search_fields = ("user__username", "skill__name")


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("user", "teach_skill", "learn_skill", "cash_price", "created_at")
    search_fields = ("user__username", "teach_skill__name", "learn_skill__name")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("user_a", "user_b", "teach_a_learn_b", "teach_b_learn_a", "created_at")
    search_fields = ("user_a__username", "user_b__username")

@admin.register(SwipeAction)
class SwipeActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'teaching_class', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'teaching_class__title')
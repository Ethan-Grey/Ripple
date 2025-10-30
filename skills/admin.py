from django.contrib import admin
from .models import Skill, UserSkill, Offer, Match, TeachingClass, ClassTopic, ClassEnrollment, ClassReview, ClassTradeOffer, TeacherApplication


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


@admin.register(TeachingClass)
class TeachingClassAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "difficulty", "duration_minutes", "price_cents", "is_tradeable", "is_published", "avg_rating", "reviews_count", "created_at")
    list_filter = ("difficulty", "is_tradeable", "is_published")
    search_fields = ("title", "teacher__username")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ClassTopic)
class ClassTopicAdmin(admin.ModelAdmin):
    list_display = ("teaching_class", "name")
    search_fields = ("teaching_class__title", "name")


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "teaching_class", "status", "granted_via", "purchase_id", "created_at")
    list_filter = ("status", "granted_via")
    search_fields = ("user__username", "teaching_class__title", "purchase_id")


@admin.register(ClassReview)
class ClassReviewAdmin(admin.ModelAdmin):
    list_display = ("teaching_class", "reviewer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("teaching_class__title", "reviewer__username")


@admin.register(ClassTradeOffer)
class ClassTradeOfferAdmin(admin.ModelAdmin):
    list_display = ("proposer", "receiver", "offered_class", "requested_class", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("proposer__username", "receiver__username", "offered_class__title", "requested_class__title")


@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant", "title", "status", "reviewer", "reviewed_at", "created_at")
    list_filter = ("status",)
    search_fields = ("applicant__username", "title")

from django.contrib import admin
from .models import Skill, SwipeAction, UserSkill, Offer, Match, ClassTimeSlot, ClassBooking, ClassFavorite, ClassReview


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


@admin.register(ClassTimeSlot)
class ClassTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('teaching_class', 'start_time', 'end_time', 'max_students', 'is_active', 'get_available_spots')
    list_filter = ('is_active', 'is_recurring', 'start_time')
    search_fields = ('teaching_class__title', 'teaching_class__teacher__username')
    date_hierarchy = 'start_time'
    
    def get_available_spots(self, obj):
        return obj.get_available_spots()
    get_available_spots.short_description = 'Available Spots'


@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'time_slot', 'status', 'created_at', 'time_slot__start_time')
    list_filter = ('status', 'created_at')
    search_fields = ('student__username', 'time_slot__teaching_class__title')
    date_hierarchy = 'created_at'

@admin.register(ClassFavorite)
class ClassFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'teaching_class', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'teaching_class__title')

@admin.register(ClassReview)
class ClassReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'teaching_class', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__username', 'teaching_class__title')
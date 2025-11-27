from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Evidence


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "verification_status")
    list_filter = ("verification_status",)
    search_fields = ("user__username", "user__email", "location")
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio', 'location', 'avatar')
        }),
        ('Verification', {
            'fields': ('verification_status',)
        }),
    )


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("profile", "title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "profile__user__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

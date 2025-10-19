from django.contrib import admin
from django.utils import timezone
from .models import Community, CommunityRequest, Post, Comment


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ("name", "skill", "creator", "member_count", "post_count", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at", "skill")
    search_fields = ("name", "skill__name", "creator__username")
    readonly_fields = ("created_at", "updated_at")
    
    def member_count(self, obj):
        return obj.member_count
    member_count.short_description = "Members"
    
    def post_count(self, obj):
        return obj.post_count
    post_count.short_description = "Posts"


@admin.register(CommunityRequest)
class CommunityRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "skill", "requester", "status", "created_at", "reviewed_by")
    list_filter = ("status", "created_at", "skill")
    search_fields = ("name", "requester__username", "skill__name")
    readonly_fields = ("created_at", "reviewed_at")
    actions = ["approve_requests", "reject_requests"]
    
    def approve_requests(self, request, queryset):
        for req in queryset.filter(status='pending'):
            # Create the community
            community = Community.objects.create(
                name=req.name,
                skill=req.skill,
                description=req.description,
                creator=req.requester,
                is_approved=True
            )
            # Add requester as first member
            community.members.add(req.requester)
            
            # Update request status
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
        
        self.message_user(request, f"{queryset.count()} request(s) approved and communities created.")
    approve_requests.short_description = "Approve selected requests and create communities"
    
    def reject_requests(self, request, queryset):
        count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{count} request(s) rejected.")
    reject_requests.short_description = "Reject selected requests"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "community", "author", "score", "comment_count", "is_pinned", "created_at")
    list_filter = ("community", "is_pinned", "created_at")
    search_fields = ("title", "content", "author__username", "community__name")
    readonly_fields = ("created_at", "updated_at", "score", "comment_count")
    actions = ["pin_posts", "unpin_posts"]
    
    def score(self, obj):
        return obj.score
    score.short_description = "Score"
    
    def comment_count(self, obj):
        return obj.comment_count
    comment_count.short_description = "Comments"
    
    def pin_posts(self, request, queryset):
        queryset.update(is_pinned=True)
        self.message_user(request, f"{queryset.count()} post(s) pinned.")
    pin_posts.short_description = "Pin selected posts"
    
    def unpin_posts(self, request, queryset):
        queryset.update(is_pinned=False)
        self.message_user(request, f"{queryset.count()} post(s) unpinned.")
    unpin_posts.short_description = "Unpin selected posts"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "score", "created_at", "parent")
    list_filter = ("created_at", "post__community")
    search_fields = ("content", "author__username", "post__title")
    readonly_fields = ("created_at", "updated_at", "score")
    
    def score(self, obj):
        return obj.score
    score.short_description = "Score"

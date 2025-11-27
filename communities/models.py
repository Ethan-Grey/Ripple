from django.db import models
from django.conf import settings
from skills.models import Skill


class Community(models.Model):
    name = models.CharField(max_length=140)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_communities')
    is_approved = models.BooleanField(default=True)  # For admin approval system
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(null=True, blank=True)  # When it was deleted
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_communities')

    class Meta:
        verbose_name_plural = 'Communities'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.skill.name})"
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def post_count(self):
        return self.posts.count()


class CommunityRequest(models.Model):
    """Request to create a new community - requires admin approval"""
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending Review'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_requests')
    name = models.CharField(max_length=140)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    description = models.TextField()
    reason = models.TextField(help_text="Why do you want to create this community?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_requests')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"


class Post(models.Model):
    """Reddit-style posts in communities"""
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=300)
    content = models.TextField()
    image = models.ImageField(upload_to='community_posts/', blank=True, null=True)
    link = models.URLField(blank=True, help_text="External link (optional)")
    upvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='upvoted_posts', blank=True)
    downvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='downvoted_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(null=True, blank=True)  # When it was deleted
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_posts')
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"
    
    @property
    def score(self):
        return self.upvotes.count() - self.downvotes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()


class Comment(models.Model):
    """Reddit-style comments on posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='community_comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    upvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='upvoted_comments', blank=True)
    downvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='downvoted_comments', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"
    
    @property
    def score(self):
        return self.upvotes.count() - self.downvotes.count()

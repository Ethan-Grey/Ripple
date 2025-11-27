from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Report(models.Model):
    """Model for user reports on any content"""
    
    REASON_CHOICES = [
        ('spam', 'Spam or Misleading'),
        ('harassment', 'Harassment or Bullying'),
        ('hate_speech', 'Hate Speech'),
        ('inappropriate', 'Inappropriate Content'),
        ('impersonation', 'Impersonation'),
        ('violence', 'Violence or Threats'),
        ('scam', 'Scam or Fraud'),
        ('fake_skills', 'Fake Skills/Credentials'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    ACTION_CHOICES = [
        ('none', 'No Action Taken'),
        ('warning', 'Warning Issued'),
        ('content_removed', 'Content Removed'),
        ('user_suspended', 'User Suspended'),
        ('user_banned', 'User Banned'),
    ]
    
    # Reporter info
    reporter = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reports_made'
    )
    
    # Reported content (generic relation to any model)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    reported_object = GenericForeignKey('content_type', 'object_id')
    
    # Report details
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(help_text="Please provide details about the issue")
    
    # Admin handling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='none')
    admin_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reports_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"Report by {self.reporter.username} - {self.get_reason_display()}"
    
    def get_reported_object_display(self):
        """Get a human-readable description of what was reported"""
        # Check if the object still exists (might be deleted)
        try:
            reported_obj = self.reported_object
            if reported_obj is None:
                # Object was deleted
                if self.content_type.model == 'user':
                    return f"User: [Deleted] (ID: {self.object_id})"
                elif self.content_type.model == 'community':
                    return f"Community: [Deleted] (ID: {self.object_id})"
                elif self.content_type.model == 'teachingclass':
                    return f"Class: [Deleted] (ID: {self.object_id})"
                elif self.content_type.model == 'post':
                    return f"Post: [Deleted] (ID: {self.object_id})"
                elif self.content_type.model == 'message':
                    return f"Message: [Deleted] (ID: {self.object_id})"
                else:
                    return f"{self.content_type.model.title()}: [Deleted] (ID: {self.object_id})"
        except Exception:
            # Object doesn't exist anymore
            if self.content_type.model == 'user':
                return f"User: [Deleted] (ID: {self.object_id})"
            elif self.content_type.model == 'community':
                return f"Community: [Deleted] (ID: {self.object_id})"
            elif self.content_type.model == 'teachingclass':
                return f"Class: [Deleted] (ID: {self.object_id})"
            elif self.content_type.model == 'post':
                return f"Post: [Deleted] (ID: {self.object_id})"
            elif self.content_type.model == 'message':
                return f"Message: [Deleted] (ID: {self.object_id})"
            else:
                return f"{self.content_type.model.title()}: [Deleted] (ID: {self.object_id})"
        
        # Object exists, return normal display
        if self.content_type.model == 'user':
            return f"User: {reported_obj.username}"
        elif self.content_type.model == 'community':
            return f"Community: {reported_obj.name}"
        elif self.content_type.model == 'teachingclass':
            return f"Class: {reported_obj.title}"
        elif self.content_type.model == 'post':
            return f"Post: {reported_obj.title}"
        elif self.content_type.model == 'message':
            return f"Message in conversation"
        else:
            return f"{self.content_type.model.title()}"


class UserWarning(models.Model):
    """Track warnings issued to users"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings')
    issued_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='warnings_issued'
    )
    related_report = models.ForeignKey(
        Report, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='warnings'
    )
    
    reason = models.CharField(max_length=200)
    description = models.TextField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Warning for {self.user.username} - {self.reason}"
    

    
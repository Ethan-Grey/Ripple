from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Represents a conversation between users"""
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return f"Conversation {self.id} - {self.participants.count()} participants"
    
    def get_other_participant(self, user):
        """Get the other participant in a 1-on-1 conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_latest_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.order_by('-timestamp').first()


class Message(models.Model):
    """Represents a single message in a conversation"""
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, 
        choices=MESSAGE_TYPES, 
        default='text'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Deprecated - use MessageStatus instead
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', '-timestamp']),
            models.Index(fields=['conversation', 'sender']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} in conversation {self.conversation.id}"
    
    def mark_as_read(self, user):
        """Mark this message as read by a specific user (deprecated - use MessageStatus)"""
        if not self.is_read and self.sender != user:
            self.is_read = True
            self.save()
    
    def mark_as_read_for_user(self, user):
        """Mark this message as read for a specific user using MessageStatus"""
        if self.sender == user:
            return  # Don't mark own messages as read
        
        status, created = MessageStatus.objects.get_or_create(
            message=self,
            user=user,
            defaults={'is_read': True, 'read_at': timezone.now()}
        )
        if not created and not status.is_read:
            status.is_read = True
            status.read_at = timezone.now()
            status.save()
    
    def is_read_by_user(self, user):
        """Check if message is read by a specific user"""
        if self.sender == user:
            return True  # Own messages are considered "read"
        try:
            status = self.statuses.get(user=user)
            return status.is_read
        except MessageStatus.DoesNotExist:
            return False


class MessageStatus(models.Model):
    """Tracks read status of messages for each user"""
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='statuses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='message_statuses'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['message', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.message.id} - {'Read' if self.is_read else 'Unread'}"
    
    def mark_as_read(self):
        """Mark this message as read for this user"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class ConversationUserStatus(models.Model):
    """Tracks user-specific conversation states (archived, deleted)"""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='user_statuses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_statuses'
    )
    is_archived = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['user', 'is_archived']),
            models.Index(fields=['user', 'is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Conversation {self.conversation.id} - Archived: {self.is_archived}, Deleted: {self.is_deleted}"
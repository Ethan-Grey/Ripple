from django.contrib import admin
from .models import Conversation, Message, MessageStatus


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'participants_list', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['participants__username', 'participants__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def participants_list(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    participants_list.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'message_type', 'timestamp', 'is_read']
    list_filter = ['message_type', 'is_read', 'timestamp']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'message', 'is_read', 'read_at']
    list_filter = ['is_read', 'read_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['read_at']
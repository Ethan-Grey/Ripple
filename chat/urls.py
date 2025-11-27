from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.messages_page, name='messages'),
    path('conversation/<int:conversation_id>/', views.conversation, name='conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
    path('conversation/<int:conversation_id>/archive/', views.archive_conversation, name='archive_conversation'),
    path('conversation/<int:conversation_id>/unarchive/', views.unarchive_conversation, name='unarchive_conversation'),
    path('conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/conversation/<int:conversation_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('api/conversations/update/', views.get_conversations_update, name='get_conversations_update'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]

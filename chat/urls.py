from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.messages_page, name='messages'),
    path('conversation/<int:conversation_id>/', views.conversation, name='conversation'),
    path('conversation/<int:conversation_id>/send/', views.send_message, name='send_message'),
]

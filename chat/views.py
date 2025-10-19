from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from .models import Conversation, Message
from django.http import JsonResponse

@login_required
def messages_page(request):
    """Main messages page with conversation list and chat"""
    # Get or create conversation if username is provided
    other_user = None
    if request.GET.get('user'):
        try:
            # Support both username and user_id
            user_param = request.GET.get('user')
            if user_param.isdigit():
                other_user = User.objects.get(id=user_param)
            else:
                other_user = User.objects.get(username=user_param)
            
            if other_user != request.user:
                conversation = get_or_create_conversation(request.user, other_user)
                return redirect('chat:conversation', conversation_id=conversation.id)
        except User.DoesNotExist:
            pass
    
    # Get all conversations for the current user
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'messages').distinct()
    
    # Get selected conversation
    conversation_id = request.GET.get('conversation')
    selected_conversation = None
    messages = []
    
    if conversation_id:
        selected_conversation = conversations.filter(id=conversation_id).first()
        if selected_conversation:
            messages = selected_conversation.messages.select_related('sender').all()
            # Mark messages as read
            selected_conversation.messages.exclude(
                sender=request.user
            ).update(is_read=True)
    
    # Add unread count to each conversation
    for conv in conversations:
        conv.unread_count = conv.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
        conv.other_user = conv.get_other_participant(request.user)
        conv.latest_message = conv.get_latest_message()
    
    context = {
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'messages': messages,
        'other_user': selected_conversation.get_other_participant(request.user) if selected_conversation else None,
    }
    return render(request, 'chat/messages.html', context)

@login_required
def conversation(request, conversation_id):
    """View a specific conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    return redirect(f'/chat/messages/?conversation={conversation_id}')

@login_required
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    if request.method == 'POST':
        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            participants=request.user
        )
        
        content = request.POST.get('content', '').strip()
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender': message.sender.username,
                        'timestamp': message.timestamp.strftime('%H:%M')
                    }
                })
        
        return redirect(f'/chat/messages/?conversation={conversation_id}')
    
    return redirect('chat:messages')

def get_or_create_conversation(user1, user2):
    """Get existing conversation or create new one between two users"""
    conversation = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)
    
    return conversation
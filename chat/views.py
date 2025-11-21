from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max, Prefetch, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from .models import Conversation, Message, MessageStatus, ConversationUserStatus
from django.http import JsonResponse
from django.utils import timezone

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
    
    # Check if viewing archived conversations
    view_archived = request.GET.get('archived', 'false').lower() == 'true'
    
    # Get all conversations for the current user with optimized queries
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related(
        'participants',
        Prefetch(
            'messages',
            queryset=Message.objects.select_related('sender').order_by('-timestamp')[:1],
            to_attr='latest_messages'
        )
    ).distinct()
    
    # Filter out deleted conversations
    deleted_statuses = ConversationUserStatus.objects.filter(
        user=request.user,
        is_deleted=True
    ).values_list('conversation_id', flat=True)
    conversations = conversations.exclude(id__in=deleted_statuses)
    
    # Filter archived conversations based on view mode
    if view_archived:
        # Show only archived conversations
        archived_statuses = ConversationUserStatus.objects.filter(
            user=request.user,
            is_archived=True
        ).values_list('conversation_id', flat=True)
        conversations = conversations.filter(id__in=archived_statuses)
    else:
        # Exclude archived conversations
        archived_statuses = ConversationUserStatus.objects.filter(
            user=request.user,
            is_archived=True
        ).values_list('conversation_id', flat=True)
        conversations = conversations.exclude(id__in=archived_statuses)
    
    # Get selected conversation
    conversation_id = request.GET.get('conversation')
    selected_conversation = None
    messages = []
    page_obj = None
    last_message_id = 0
    
    if conversation_id:
        selected_conversation = conversations.filter(id=conversation_id).first()
        if selected_conversation:
            # Get messages with pagination
            messages_queryset = selected_conversation.messages.select_related('sender').order_by('timestamp')
            paginator = Paginator(messages_queryset, 50)  # 50 messages per page
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            messages = list(page_obj.object_list)  # Convert to list for negative indexing
            
            # Get last message ID for polling
            if messages:
                last_message_id = messages[-1].id
            else:
                # If no messages on this page, get the latest message ID from the conversation
                latest_msg = selected_conversation.messages.order_by('-timestamp').first()
                last_message_id = latest_msg.id if latest_msg else 0
            
            # Mark messages as read using MessageStatus
            unread_messages = selected_conversation.messages.exclude(sender=request.user)
            for message in unread_messages:
                message.mark_as_read_for_user(request.user)
    
    # Add computed fields to each conversation (optimized)
    for conv in conversations:
        # Get unread count using MessageStatus
        conv.unread_count = MessageStatus.objects.filter(
            message__conversation=conv,
            user=request.user,
            is_read=False
        ).exclude(
            message__sender=request.user
        ).count()
        
        conv.other_user = conv.get_other_participant(request.user)
        conv.latest_message = conv.get_latest_message()
    
    context = {
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'messages': messages,
        'page_obj': page_obj,
        'last_message_id': last_message_id,
        'other_user': selected_conversation.get_other_participant(request.user) if selected_conversation else None,
        'view_archived': view_archived,
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
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=['updated_at'])
            
            # Create MessageStatus for other participants (unread)
            other_participants = conversation.participants.exclude(id=request.user.id)
            for participant in other_participants:
                MessageStatus.objects.get_or_create(
                    message=message,
                    user=participant,
                    defaults={'is_read': False}
                )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender': message.sender.username,
                        'sender_id': message.sender.id,
                        'timestamp': message.timestamp.strftime('%H:%M'),
                        'full_timestamp': message.timestamp.isoformat(),
                    }
                })
        
        return redirect(f'/chat/messages/?conversation={conversation_id}')
    
    return redirect('chat:messages')

def get_or_create_conversation(user1, user2):
    """Get existing conversation or create new one between two users"""
    # Optimized query to find existing conversation
    conversation = Conversation.objects.filter(
        participants=user1
    ).filter(
        participants=user2
    ).prefetch_related('participants').first()
    
    if conversation:
        # Check if conversation is deleted for either user and restore it
        for user in [user1, user2]:
            try:
                status = ConversationUserStatus.objects.get(
                    conversation=conversation,
                    user=user
                )
                if status.is_deleted:
                    # Restore the conversation by un-deleting it
                    status.is_deleted = False
                    status.deleted_at = None
                    status.is_archived = False  # Also un-archive if it was archived
                    status.archived_at = None
                    status.save()
            except ConversationUserStatus.DoesNotExist:
                # No status record, conversation is not deleted
                pass
    else:
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(user1, user2)
    
    return conversation


@login_required
def get_new_messages(request, conversation_id):
    """AJAX endpoint to get new messages since last_message_id"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    last_message_id = request.GET.get('last_message_id', 0)
    try:
        last_message_id = int(last_message_id)
    except (ValueError, TypeError):
        last_message_id = 0
    
    # Get messages newer than last_message_id
    new_messages = conversation.messages.filter(
        id__gt=last_message_id
    ).select_related('sender').order_by('timestamp')
    
    # Mark as read
    for message in new_messages.exclude(sender=request.user):
        message.mark_as_read_for_user(request.user)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'full_timestamp': msg.timestamp.isoformat(),
        'is_sent': msg.sender.id == request.user.id,
    } for msg in new_messages]
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'count': len(messages_data)
    })


@login_required
def get_conversations_update(request):
    """AJAX endpoint to get updated conversation list"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related('participants').distinct()
    
    # Filter out deleted conversations
    deleted_statuses = ConversationUserStatus.objects.filter(
        user=request.user,
        is_deleted=True
    ).values_list('conversation_id', flat=True)
    conversations = conversations.exclude(id__in=deleted_statuses)
    
    # Check if viewing archived
    view_archived = request.GET.get('archived', 'false').lower() == 'true'
    if view_archived:
        archived_statuses = ConversationUserStatus.objects.filter(
            user=request.user,
            is_archived=True
        ).values_list('conversation_id', flat=True)
        conversations = conversations.filter(id__in=archived_statuses)
    else:
        archived_statuses = ConversationUserStatus.objects.filter(
            user=request.user,
            is_archived=True
        ).values_list('conversation_id', flat=True)
        conversations = conversations.exclude(id__in=archived_statuses)
    
    conversations_data = []
    for conv in conversations:
        latest_msg = conv.get_latest_message()
        unread_count = MessageStatus.objects.filter(
            message__conversation=conv,
            user=request.user,
            is_read=False
        ).exclude(
            message__sender=request.user
        ).count()
        
        other_user = conv.get_other_participant(request.user)
        conversations_data.append({
            'id': conv.id,
            'other_user': {
                'id': other_user.id if other_user else None,
                'username': other_user.username if other_user else '',
                'name': f"{other_user.first_name} {other_user.last_name}".strip() if other_user else '',
            },
            'latest_message': {
                'content': latest_msg.content[:50] if latest_msg else '',
                'timestamp': latest_msg.timestamp.isoformat() if latest_msg else None,
            } if latest_msg else None,
            'unread_count': unread_count,
            'updated_at': conv.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'conversations': conversations_data
    })


@login_required
def archive_conversation(request, conversation_id):
    """Archive a conversation for the current user"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    status, created = ConversationUserStatus.objects.get_or_create(
        conversation=conversation,
        user=request.user,
        defaults={'is_archived': True, 'archived_at': timezone.now()}
    )
    
    if not created:
        status.is_archived = True
        status.archived_at = timezone.now()
        status.is_deleted = False  # Un-delete if it was deleted
        status.deleted_at = None
        status.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:messages')


@login_required
def unarchive_conversation(request, conversation_id):
    """Unarchive a conversation for the current user"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    try:
        status = ConversationUserStatus.objects.get(
            conversation=conversation,
            user=request.user
        )
        status.is_archived = False
        status.archived_at = None
        status.save()
    except ConversationUserStatus.DoesNotExist:
        pass
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:messages')


@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation for the current user"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    status, created = ConversationUserStatus.objects.get_or_create(
        conversation=conversation,
        user=request.user,
        defaults={'is_deleted': True, 'deleted_at': timezone.now()}
    )
    
    if not created:
        status.is_deleted = True
        status.deleted_at = timezone.now()
        status.is_archived = False  # Un-archive if it was archived
        status.archived_at = None
        status.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:messages')
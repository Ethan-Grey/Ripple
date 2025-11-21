const conversationId = {% if selected_conversation %}{{ selected_conversation.id }}{% else %}null{% endif %};
let lastMessageId = {{ last_message_id|default:"0" }};
let pollingInterval = null;
let isPolling = false;

// Auto-scroll to bottom of messages
const messagesArea = document.getElementById('messagesArea');
if (messagesArea && messagesArea.children.length > 0) {
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// AJAX message sending
const messageForm = document.getElementById('messageForm');
if (messageForm) {
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const input = this.querySelector('input[name="content"]');
        const content = input.value.trim();
        
        if (!content || !conversationId) {
            return;
        }
        
        // Disable form while sending
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalHTML = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>Sending...';
        
        // Send via AJAX
        fetch(`{% url 'chat:send_message' 0 %}`.replace('0', conversationId), {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `content=${encodeURIComponent(content)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear input
                input.value = '';
                
                // Add message to UI immediately
                addMessageToUI(data.message, true);
                
                // Update last message ID
                lastMessageId = data.message.id;
            } else {
                alert('Failed to send message. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to send message. Please try again.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;
        });
    });
}

// Add message to UI
function addMessageToUI(messageData, isSent) {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;
    
    // Remove "no messages" placeholder if exists
    const noMessages = messagesArea.querySelector('.no-messages');
    if (noMessages) {
        noMessages.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
    messageDiv.dataset.messageId = messageData.id;
    
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-content">${escapeHtml(messageData.content)}</div>
            <div class="message-time">${messageData.timestamp}</div>
        </div>
    `;
    
    messagesArea.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Poll for new messages
function pollForNewMessages() {
    if (!conversationId || isPolling) return;
    
    isPolling = true;
    fetch(`{% url 'chat:get_new_messages' 0 %}?last_message_id=${lastMessageId}`.replace('0', conversationId))
        .then(response => response.json())
        .then(data => {
            if (data.success && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    addMessageToUI(msg, msg.is_sent);
                    lastMessageId = Math.max(lastMessageId, msg.id);
                });
                
                // Update unread counts in sidebar
                updateConversationsList();
            }
        })
        .catch(error => {
            console.error('Polling error:', error);
        })
        .finally(() => {
            isPolling = false;
        });
}

// Update conversations list
function updateConversationsList() {
    fetch('{% url "chat:get_conversations_update" %}')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update unread badges in sidebar
                data.conversations.forEach(conv => {
                    const convItem = document.querySelector(`.conversation-item[href*="conversation=${conv.id}"]`);
                    if (convItem) {
                        const badge = convItem.querySelector('.unread-badge');
                        if (conv.unread_count > 0) {
                            if (!badge) {
                                const meta = convItem.querySelector('.conversation-meta');
                                const badgeEl = document.createElement('span');
                                badgeEl.className = 'unread-badge';
                                badgeEl.textContent = conv.unread_count;
                                meta.appendChild(badgeEl);
                            } else {
                                badge.textContent = conv.unread_count;
                            }
                        } else if (badge) {
                            badge.remove();
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Update conversations error:', error);
        });
}

// Start polling when conversation is selected
if (conversationId) {
    // Poll every 3 seconds
    pollingInterval = setInterval(pollForNewMessages, 3000);
    
    // Also poll immediately
    setTimeout(pollForNewMessages, 1000);
    
    // Update conversations list every 5 seconds
    setInterval(updateConversationsList, 5000);
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
});

// Modal functions
let pendingConversationId = null;
let pendingAction = null;

function showArchiveModal(conversationId) {
    pendingConversationId = conversationId;
    pendingAction = 'archive';
    
    document.getElementById('modalIcon').innerHTML = '<i class="bi bi-archive" style="color: #667eea;"></i>';
    document.getElementById('modalTitle').textContent = 'Archive Conversation';
    document.getElementById('modalMessage').textContent = 'Are you sure you want to archive this conversation? You can view it later in the archived section.';
    document.getElementById('confirmActionBtn').textContent = 'Archive';
    document.getElementById('confirmActionBtn').style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

function showUnarchiveModal(conversationId) {
    pendingConversationId = conversationId;
    pendingAction = 'unarchive';
    
    document.getElementById('modalIcon').innerHTML = '<i class="bi bi-inbox" style="color: #10b981;"></i>';
    document.getElementById('modalTitle').textContent = 'Unarchive Conversation';
    document.getElementById('modalMessage').textContent = 'Are you sure you want to unarchive this conversation? It will be moved back to your active conversations.';
    document.getElementById('confirmActionBtn').textContent = 'Unarchive';
    document.getElementById('confirmActionBtn').style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

function showDeleteModal(conversationId) {
    pendingConversationId = conversationId;
    pendingAction = 'delete';
    
    document.getElementById('modalIcon').innerHTML = '<i class="bi bi-trash" style="color: #ef4444;"></i>';
    document.getElementById('modalTitle').textContent = 'Delete Conversation';
    document.getElementById('modalMessage').textContent = 'Are you sure you want to delete this conversation? This action cannot be undone and all messages will be permanently removed.';
    document.getElementById('confirmActionBtn').textContent = 'Delete';
    document.getElementById('confirmActionBtn').style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
    
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

// Handle modal confirmation
const confirmBtn = document.getElementById('confirmActionBtn');
let confirmHandler = null;

function setupConfirmHandler() {
    if (confirmHandler) {
        confirmBtn.removeEventListener('click', confirmHandler);
    }
    
    confirmHandler = function() {
        if (!pendingConversationId || !pendingAction) return;
        
        const conversationId = pendingConversationId;
        const action = pendingAction;
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmationModal'));
        modal.hide();
        
        // Execute action
        if (action === 'archive') {
            archiveConversation(conversationId);
        } else if (action === 'unarchive') {
            unarchiveConversation(conversationId);
        } else if (action === 'delete') {
            deleteConversation(conversationId);
        }
        
        // Reset
        pendingConversationId = null;
        pendingAction = null;
    };
    
    confirmBtn.addEventListener('click', confirmHandler);
}

// Initialize on page load
setupConfirmHandler();

// Archive conversation
function archiveConversation(conversationId) {
    fetch(`{% url 'chat:archive_conversation' 0 %}`.replace('0', conversationId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '{% url "chat:messages" %}';
        } else {
            showErrorModal('Failed to archive conversation. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorModal('Failed to archive conversation. Please try again.');
    });
}

// Unarchive conversation
function unarchiveConversation(conversationId) {
    fetch(`{% url 'chat:unarchive_conversation' 0 %}`.replace('0', conversationId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '{% url "chat:messages" %}';
        } else {
            showErrorModal('Failed to unarchive conversation. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorModal('Failed to unarchive conversation. Please try again.');
    });
}

// Delete conversation
function deleteConversation(conversationId) {
    fetch(`{% url 'chat:delete_conversation' 0 %}`.replace('0', conversationId), {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '{% url "chat:messages" %}';
        } else {
            showErrorModal('Failed to delete conversation. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorModal('Failed to delete conversation. Please try again.');
    });
}

// Show error modal (reuse confirmation modal)
function showErrorModal(message) {
    // Remove existing handler temporarily
    if (confirmHandler) {
        confirmBtn.removeEventListener('click', confirmHandler);
    }
    
    document.getElementById('modalIcon').innerHTML = '<i class="bi bi-exclamation-triangle" style="color: #ef4444;"></i>';
    document.getElementById('modalTitle').textContent = 'Error';
    document.getElementById('modalMessage').textContent = message;
    confirmBtn.textContent = 'OK';
    confirmBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    
    const errorHandler = function() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmationModal'));
        modal.hide();
        confirmBtn.removeEventListener('click', errorHandler);
        // Restore normal handler
        setupConfirmHandler();
    };
    
    confirmBtn.addEventListener('click', errorHandler);
    
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

// Swipe functionality for conversation items
(function() {
    const SWIPE_THRESHOLD = 30; // Minimum swipe distance to keep swiped
    const MAX_SWIPE = 170; // Maximum swipe distance (85px * 2 buttons)
    
    function initSwipe() {
        const conversationItems = document.querySelectorAll('.conversation-item');
        
        conversationItems.forEach(item => {
            let swipeStartX = 0;
            let swipeCurrentX = 0;
            let isSwipeActive = false;
            let hasSwiped = false;
            let startTime = 0;
            let justSwiped = false; // Flag to prevent click handler from interfering

            // Mouse events
            item.addEventListener('mousedown', (e) => {
                // Don't start swipe if clicking on action buttons
                if (e.target.closest('.conversation-actions')) {
                    return;
                }
                swipeStartX = e.clientX;
                startTime = Date.now();
                isSwipeActive = true;
                justSwiped = false;
                item.classList.add('swiping');
                e.preventDefault();
                e.stopPropagation();
            });

            document.addEventListener('mousemove', (e) => {
                if (!isSwipeActive || !item.classList.contains('swiping')) return;
                
                swipeCurrentX = e.clientX - swipeStartX;
                
                // Only allow swiping left (negative values)
                if (swipeCurrentX > 0) {
                    swipeCurrentX = 0;
                } else if (Math.abs(swipeCurrentX) > MAX_SWIPE) {
                    swipeCurrentX = -MAX_SWIPE;
                }
                
                item.style.transform = `translateX(${swipeCurrentX}px)`;
                hasSwiped = Math.abs(swipeCurrentX) > 10;
            });

            document.addEventListener('mouseup', (e) => {
                if (!isSwipeActive) return;
                
                const swipeTime = Date.now() - startTime;
                const currentSwipeX = swipeCurrentX; // Save current value before resetting
                const wasDragging = hasSwiped || Math.abs(swipeCurrentX) > 10;
                
                isSwipeActive = false;
                item.classList.remove('swiping');
                
                // If user dragged left (swiped), keep it at the current position
                if (wasDragging && currentSwipeX < 0) {
                    // Keep it swiped at current position (or max if beyond)
                    const finalX = Math.abs(currentSwipeX) > MAX_SWIPE ? -MAX_SWIPE : currentSwipeX;
                    // Re-enable transition for smooth snap
                    item.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    item.style.transform = `translateX(${finalX}px)`;
                    justSwiped = true;
                    
                    // Close other swiped items
                    conversationItems.forEach(otherItem => {
                        if (otherItem !== item && otherItem.style.transform && otherItem.style.transform.includes('translateX')) {
                            otherItem.style.transform = '';
                        }
                    });
                    
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Reset flag after a short delay to allow click handler to work later
                    setTimeout(() => {
                        justSwiped = false;
                    }, 100);
                } else if (!wasDragging && swipeTime < 200 && Math.abs(currentSwipeX) < 10) {
                    // Quick click (no drag), allow navigation
                    justSwiped = false;
                    const href = item.getAttribute('href');
                    if (href) {
                        window.location.href = href;
                    }
                } else {
                    // Snap back if no meaningful drag
                    justSwiped = false;
                    item.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    item.style.transform = '';
                }
                
                swipeCurrentX = 0;
                hasSwiped = false;
            });

            // Touch events
            item.addEventListener('touchstart', (e) => {
                // Don't start swipe if clicking on action buttons
                if (e.target.closest('.conversation-actions')) {
                    return;
                }
                swipeStartX = e.touches[0].clientX;
                startTime = Date.now();
                isSwipeActive = true;
                item.classList.add('swiping');
            }, { passive: true });

            item.addEventListener('touchmove', (e) => {
                if (!isSwipeActive) return;
                
                swipeCurrentX = e.touches[0].clientX - swipeStartX;
                
                // Only allow swiping left
                if (swipeCurrentX > 0) {
                    swipeCurrentX = 0;
                } else if (Math.abs(swipeCurrentX) > MAX_SWIPE) {
                    swipeCurrentX = -MAX_SWIPE;
                }
                
                item.style.transform = `translateX(${swipeCurrentX}px)`;
                hasSwiped = Math.abs(swipeCurrentX) > 10;
                
                // Prevent scrolling if swiping
                if (hasSwiped) {
                    e.preventDefault();
                }
            }, { passive: false });

            item.addEventListener('touchend', (e) => {
                if (!isSwipeActive) return;
                
                const swipeTime = Date.now() - startTime;
                const currentSwipeX = swipeCurrentX; // Save current value before resetting
                const wasDragging = hasSwiped || Math.abs(swipeCurrentX) > 10;
                
                isSwipeActive = false;
                item.classList.remove('swiping');
                
                // If user dragged left (swiped), keep it at the current position
                if (wasDragging && currentSwipeX < 0) {
                    // Keep it swiped at current position (or max if beyond)
                    const finalX = Math.abs(currentSwipeX) > MAX_SWIPE ? -MAX_SWIPE : currentSwipeX;
                    // Re-enable transition for smooth snap
                    item.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    item.style.transform = `translateX(${finalX}px)`;
                    // Close other swiped items
                    conversationItems.forEach(otherItem => {
                        if (otherItem !== item && otherItem.style.transform && otherItem.style.transform.includes('translateX')) {
                            otherItem.style.transform = '';
                        }
                    });
                    e.preventDefault();
                } else if (!wasDragging && swipeTime < 200 && Math.abs(currentSwipeX) < 10) {
                    // Quick tap (no drag), allow navigation
                    const href = item.getAttribute('href');
                    if (href) {
                        window.location.href = href;
                    }
                } else {
                    // Snap back if no meaningful drag
                    item.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                    item.style.transform = '';
                }
                
                swipeCurrentX = 0;
                hasSwiped = false;
            }, { passive: false });

            // Click handler - close swipe if clicked on item (not buttons)
            item.addEventListener('click', (e) => {
                // Don't interfere if we just swiped
                if (justSwiped) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
                
                // If buttons are visible (swiped), close on click (unless clicking buttons)
                const transform = item.style.transform;
                if (transform && transform.includes('translateX')) {
                    const match = transform.match(/-?\d+/);
                    if (match && Math.abs(parseInt(match[0])) >= SWIPE_THRESHOLD) {
                        // Don't close if clicking on action buttons
                        if (!e.target.closest('.conversation-actions')) {
                            e.preventDefault();
                            e.stopPropagation();
                            item.style.transform = '';
                            return false;
                        }
                    }
                }
            }, true);
        });

        // Close swiped items when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.conversation-swipe-wrapper')) {
                conversationItems.forEach(item => {
                    if (item.style.transform && item.style.transform.includes('translateX')) {
                        item.style.transform = '';
                    }
                });
            }
        });
    }
    
    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSwipe);
    } else {
        initSwipe();
    }
})();
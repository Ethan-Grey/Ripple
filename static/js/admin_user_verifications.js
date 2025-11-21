// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('search-input');
    if (input) {
        // Add clear search functionality
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'btn btn-outline-secondary btn-sm ms-2';
        clearButton.innerHTML = '<i class="fas fa-times"></i>';
        clearButton.title = 'Clear search';
        clearButton.style.display = 'none';
        
        // Add clear button to input group
        const inputGroup = input.closest('.input-group');
        if (inputGroup) {
            inputGroup.appendChild(clearButton);
        }
        
        input.addEventListener('input', () => {
            const query = input.value.toLowerCase().trim();
            
            // Show/hide clear button based on input
            if (query !== '') {
                clearButton.style.display = 'inline-block';
            } else {
                clearButton.style.display = 'none';
            }
            
            // Search through all cards
            const cards = document.querySelectorAll('.search-card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                const keywords = (card.getAttribute('data-keywords') || '').toLowerCase();
                
                // Check if the query matches any part of the keywords
                if (query === '' || keywords.includes(query)) {
                    card.style.display = 'block';
                    card.style.opacity = '1';
                    card.style.transform = 'scale(1)';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                    card.style.opacity = '0.5';
                    card.style.transform = 'scale(0.95)';
                }
            });
            
            // Update the results count
            const countBadge = document.querySelector('.badge.bg-secondary');
            if (countBadge) {
                countBadge.textContent = `${visibleCount} user${visibleCount !== 1 ? 's' : ''}`;
            }
            
            // Show no results message if needed
            const noResultsCard = document.querySelector('.no-results-message');
            if (visibleCount === 0 && query !== '') {
                if (!noResultsCard) {
                    const noResults = document.createElement('div');
                    noResults.className = 'card no-results-message';
                    noResults.innerHTML = `
                        <div class="card-body text-center py-5">
                            <i class="fas fa-search fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No users found</h5>
                            <p class="text-muted">No users match your search criteria.</p>
                        </div>
                    `;
                    const container = document.querySelector('.container .row .col-12');
                    container.appendChild(noResults);
                }
            } else if (noResultsCard) {
                noResultsCard.remove();
            }
        });
        
        clearButton.addEventListener('click', () => {
            input.value = '';
            input.dispatchEvent(new Event('input'));
        });
    }
});

// Handle verification actions with AJAX and modal
let currentActionData = null;

document.addEventListener('DOMContentLoaded', function() {
    const actionButtons = document.querySelectorAll('.verification-action-btn');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const profileId = this.dataset.profileId;
            const action = this.dataset.action;
            const username = this.dataset.username;
            
            // Store current action data
            currentActionData = {
                profileId: profileId,
                action: action,
                username: username,
                button: this
            };
            
            // Show modal with appropriate content
            showVerificationModal(action, username);
        });
    });
    
    // Handle confirm action button
    document.getElementById('confirmActionBtn').addEventListener('click', function() {
        if (currentActionData) {
            performVerificationAction(currentActionData);
        }
    });
    
    // Clear current action data when modal is hidden
    document.getElementById('verificationActionModal').addEventListener('hidden.bs.modal', function() {
        currentActionData = null;
    });
});

function showVerificationModal(action, username) {
    const modal = document.getElementById('verificationActionModal');
    const modalHeader = document.getElementById('modal-header');
    const modalTitleText = document.getElementById('modal-title-text');
    const modalIcon = document.getElementById('modal-icon');
    const modalMessage = document.getElementById('modal-message');
    const modalWarning = document.getElementById('modal-warning');
    const confirmBtn = document.getElementById('confirmActionBtn');
    const confirmBtnText = document.getElementById('confirm-btn-text');
    
    if (action === 'approve') {
        // Approve action
        modalHeader.className = 'modal-header bg-success text-white';
        modalTitleText.textContent = 'Approve Verification';
        modalIcon.className = 'fas fa-check-circle fa-3x text-success';
        modalMessage.innerHTML = `Are you sure you want to <strong>approve</strong> <strong>${username}</strong>'s verification?`;
        modalWarning.style.display = 'none';
        confirmBtn.className = 'btn btn-success';
        confirmBtnText.textContent = 'Approve';
    } else {
        // Reject action
        modalHeader.className = 'modal-header bg-danger text-white';
        modalTitleText.textContent = 'Reject Verification';
        modalIcon.className = 'fas fa-times-circle fa-3x text-danger';
        modalMessage.innerHTML = `Are you sure you want to <strong>reject</strong> <strong>${username}</strong>'s verification?`;
        modalWarning.style.display = 'block';
        modalWarning.innerHTML = '<i class="fas fa-info-circle"></i><strong>Warning:</strong> This will delete all submitted documents and cannot be undone.';
        confirmBtn.className = 'btn btn-danger';
        confirmBtnText.textContent = 'Reject';
    }
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function performVerificationAction(actionData) {
    const { profileId, action, username, button } = actionData;
    
    // Hide modal first
    const modal = bootstrap.Modal.getInstance(document.getElementById('verificationActionModal'));
    modal.hide();
    
    if (action === 'reject') {
        // For reject action, remove the card immediately
        const card = button.closest('.search-card');
        card.style.transition = 'all 0.3s ease';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
        
        // Remove card after animation
        setTimeout(() => {
            card.remove();
            updateResultsCount();
        }, 300);
        
        // Show success message immediately
        showToast(`${username}'s verification was rejected and documents have been removed.`, 'info');
        
        // Make AJAX request in background without showing loading state
        fetch(`/users/user-verification/${profileId}/${action}/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                // If there was an error, show it
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred while processing the verification.', 'error');
        });
    } else {
        // For approve action, show loading state
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        // Make AJAX request
        fetch(`/users/user-verification/${profileId}/${action}/`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the card to show new status
                const card = button.closest('.search-card');
                card.style.opacity = '0.5';
                card.style.pointerEvents = 'none';
                
                // Update card content to show new status
                const cardHeader = card.querySelector('.card-header');
                const statusBadge = document.createElement('span');
                statusBadge.className = `badge bg-${data.verification_status === 'verified' ? 'success' : 'danger'} ms-2`;
                statusBadge.innerHTML = `<i class="fas fa-${data.verification_status === 'verified' ? 'check' : 'times'}"></i> ${data.verification_status.charAt(0).toUpperCase() + data.verification_status.slice(1)}`;
                cardHeader.querySelector('.d-flex').appendChild(statusBadge);
                
                // Show success message
                showToast(data.message, data.message_type);
                
                // Update results count
                updateResultsCount();
            } else {
                // Show error message
                showToast(data.message, 'error');
                
                // Re-enable button
                button.disabled = false;
                button.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred while processing the verification.', 'error');
            
            // Re-enable button
            button.disabled = false;
            button.innerHTML = originalText;
        });
    }
}

// Function to show toast notifications
function showToast(message, type) {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'info' ? 'info' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'info' ? 'info-circle' : 'exclamation-triangle'}"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Add toast to page
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show the toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

// Function to update results count
function updateResultsCount() {
    const visibleCards = document.querySelectorAll('.search-card:not([style*="none"])');
    const countBadge = document.querySelector('.badge.bg-secondary');
    if (countBadge) {
        countBadge.textContent = `${visibleCards.length} user${visibleCards.length !== 1 ? 's' : ''}`;
    }
}
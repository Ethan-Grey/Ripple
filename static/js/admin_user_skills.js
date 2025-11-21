let currentDeleteUrl = '';
let currentSkillBadge = null;

function deleteSkill(skillName, username, deleteUrl, skillBadge) {
    // Store the delete URL and badge element for later use
    currentDeleteUrl = deleteUrl;
    currentSkillBadge = skillBadge;
    
    // Update modal content
    document.getElementById('skillNameToDelete').textContent = skillName;
    document.getElementById('userNameToDelete').textContent = username;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('deleteSkillModal'));
    modal.show();
    
    return false;
}

// Handle confirm delete button click
document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    if (currentDeleteUrl && currentSkillBadge) {
        // Disable the button to prevent double-clicks
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
        
        // Make AJAX request
        fetch(currentDeleteUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the skill badge from the page
                currentSkillBadge.remove();
                
                // Show success message
                showToast(data.message, 'success');
                
                // Check if user has no more skills and hide the user section if needed
                checkUserSkills(currentSkillBadge);
            } else {
                // Show error message
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('An error occurred while deleting the skill.', 'error');
        })
        .finally(() => {
            // Re-enable the button
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-trash"></i> Delete Skill';
            
            // Hide the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteSkillModal'));
            modal.hide();
        });
    }
});

// Clear the delete URL when modal is hidden
document.getElementById('deleteSkillModal').addEventListener('hidden.bs.modal', function() {
    currentDeleteUrl = '';
    currentSkillBadge = null;
});

// Function to show toast notifications
function showToast(message, type) {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
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

// Function to check if user has remaining skills
function checkUserSkills(deletedBadge) {
    // Find the user container
    let userContainer = deletedBadge.closest('.border-bottom');
    if (userContainer) {
        // Check if there are any remaining skill badges in this user's section
        const remainingSkills = userContainer.querySelectorAll('.skill-badge');
        if (remainingSkills.length === 0) {
            // Hide the user section if no skills remain
            userContainer.style.opacity = '0.5';
            userContainer.style.pointerEvents = 'none';
        }
    }
}
let currentReportId = null;
let currentAction = null;

function openActionModal(reportId, action) {
    currentReportId = reportId;
    currentAction = action;
    
    const modal = document.getElementById('actionModal');
    const title = document.getElementById('modalTitle');
    const description = document.getElementById('modalDescription');
    
    const actionTexts = {
        'dismiss': {
            title: 'Dismiss Report',
            description: 'This will mark the report as dismissed with no action taken.'
        },
        'warning': {
            title: 'Issue Warning',
            description: 'This will send a warning to the reported user and mark the report as resolved.'
        },
        'remove_content': {
            title: 'Remove Content',
            description: 'This will permanently delete the reported content. This action cannot be undone.'
        },
        'suspend_user': {
            title: 'Suspend User',
            description: 'This will suspend the reported user\'s account. They will not be able to log in.'
        }
    };
    
    title.textContent = actionTexts[action].title;
    description.textContent = actionTexts[action].description;
    
    modal.classList.add('active');
}

function closeActionModal() {
    document.getElementById('actionModal').classList.remove('active');
    document.getElementById('adminNotes').value = '';
    currentReportId = null;
    currentAction = null;
}

function submitAction() {
    if (!currentReportId || !currentAction) return;
    
    const adminNotes = document.getElementById('adminNotes').value;
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/admin-handle-report/${currentReportId}/`;
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = '{{ csrf_token }}';
    
    const actionInput = document.createElement('input');
    actionInput.type = 'hidden';
    actionInput.name = 'action';
    actionInput.value = currentAction;
    
    const notesInput = document.createElement('input');
    notesInput.type = 'hidden';
    notesInput.name = 'admin_notes';
    notesInput.value = adminNotes;
    
    form.appendChild(csrfInput);
    form.appendChild(actionInput);
    form.appendChild(notesInput);
    
    document.body.appendChild(form);
    form.submit();
}

function viewReportedContent(reportId) {
    // This would open the reported content in a new tab
    alert('View content functionality - redirect to appropriate page');
}

// Close modal when clicking outside
document.getElementById('actionModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeActionModal();
    }
});
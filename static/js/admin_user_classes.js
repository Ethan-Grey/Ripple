let currentDeleteClassUrl = '';
let currentClassCard = null;

function queueDeleteClass(classTitle, teacherName, deleteUrl, classCardElement) {
    currentDeleteClassUrl = deleteUrl;
    currentClassCard = classCardElement;

    document.getElementById('classTitleToDelete').textContent = classTitle;
    document.getElementById('teacherNameToDelete').textContent = teacherName;

    const modal = new bootstrap.Modal(document.getElementById('deleteClassModal'));
    modal.show();

    return false;
}

document.getElementById('confirmDeleteClassBtn').addEventListener('click', function() {
    if (!currentDeleteClassUrl || !currentClassCard) {
        return;
    }

    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    fetch(currentDeleteClassUrl, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentClassCard.remove();
            showToast(data.message, 'success');
            checkTeacherClasses(currentClassCard);
        } else {
            showToast(data.message || 'Failed to delete class.', 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting class:', error);
        showToast('An error occurred while deleting the class.', 'error');
    })
    .finally(() => {
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-trash"></i> Delete Class';

        const modalInstance = bootstrap.Modal.getInstance(document.getElementById('deleteClassModal'));
        if (modalInstance) {
            modalInstance.hide();
        }

        currentDeleteClassUrl = '';
        currentClassCard = null;
    });
});

document.getElementById('deleteClassModal').addEventListener('hidden.bs.modal', function() {
    currentDeleteClassUrl = '';
    currentClassCard = null;
});

function showToast(message, type) {
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

    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function checkTeacherClasses(deletedCard) {
    if (!deletedCard) {
        return;
    }

    const teacherSection = deletedCard.closest('.teacher-section');
    if (!teacherSection) {
        return;
    }

    const remainingClassCards = teacherSection.querySelectorAll('.class-card');
    if (remainingClassCards.length === 0) {
        teacherSection.style.opacity = '0.5';
        teacherSection.style.pointerEvents = 'none';
    }
}
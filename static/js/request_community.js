// Add loading state to submit button
document.getElementById('requestForm').addEventListener('submit', function(e) {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.classList.add('loading');
    submitBtn.innerHTML = '<span>Submitting...</span>';
});

// Optional: Character counter for textareas
const textareas = document.querySelectorAll('textarea.form-control');
textareas.forEach(textarea => {
    textarea.addEventListener('input', function() {
        const length = this.value.length;
        console.log(`${this.id}: ${length} characters`);
    });
});
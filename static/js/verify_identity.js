// File upload feedback
document.getElementById('id_document').addEventListener('change', function(e) {
    const file = e.target.files && e.target.files[0];
    const textElement = document.getElementById('id_document_text');
    const label = e.target.closest('.upload-label');
    
    if (file) {
        textElement.innerHTML = `
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            ${file.name}
        `;
        label.classList.add('uploaded');
    }
});

document.getElementById('id_selfie').addEventListener('change', function(e) {
    const file = e.target.files && e.target.files[0];
    const textElement = document.getElementById('id_selfie_text');
    const label = e.target.closest('.upload-label');
    
    if (file) {
        textElement.innerHTML = `
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            ${file.name}
        `;
        label.classList.add('uploaded');
    }
});

document.getElementById('id_address_doc').addEventListener('change', function(e) {
    const file = e.target.files && e.target.files[0];
    const textElement = document.getElementById('id_address_doc_text');
    const label = e.target.closest('.upload-label');
    
    if (file) {
        textElement.innerHTML = `
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            ${file.name}
        `;
        label.classList.add('uploaded');
    }
});
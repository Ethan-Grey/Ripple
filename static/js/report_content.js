function updateObjectSelector() {
    const contentType = document.getElementById('contentType').value;
    const objectSection = document.getElementById('objectSection');
    
    // Hide all selectors and remove required
    document.querySelectorAll('.object-selector').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.object-selector select').forEach(sel => sel.required = false);
    
    // Show relevant selector
    if (contentType === '11') { // User
        objectSection.style.display = 'block';
        document.getElementById('userSelector').style.display = 'block';
        document.getElementById('userSelect').required = true;
    } else if (contentType === '16') { // Community
        objectSection.style.display = 'block';
        document.getElementById('communitySelector').style.display = 'block';
        document.getElementById('communitySelect').required = true;
    } else if (contentType === '14') { // Class
        objectSection.style.display = 'block';
        document.getElementById('classSelector').style.display = 'block';
        document.getElementById('classSelect').required = true;
    } else if (contentType === 'other') {
        objectSection.style.display = 'block';
        document.getElementById('otherSelector').style.display = 'block';
    } else {
        objectSection.style.display = 'none';
    }
}

function filterOptions(searchId, selectId) {
    const searchValue = document.getElementById(searchId).value.toLowerCase();
    const select = document.getElementById(selectId);
    const options = select.options;
    
    for (let i = 0; i < options.length; i++) {
        const text = options[i].text.toLowerCase();
        if (text.includes(searchValue)) {
            options[i].style.display = '';
        } else {
            options[i].style.display = 'none';
        }
    }
}

// NEW: Fill search box when double-clicking a select option
function fillSearchFromSelect(selectId, searchId) {
    const select = document.getElementById(selectId);
    const searchInput = document.getElementById(searchId);
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption) {
        // Fill the search box with the selected option's text
        searchInput.value = selectedOption.text;
        
        // Trigger the filter to show matching items
        filterOptions(searchId, selectId);
        
        // Visual feedback
        searchInput.style.background = '#d1fae5';
        setTimeout(() => {
            searchInput.style.background = '';
        }, 300);
        
        // Focus the search input
        searchInput.focus();
    }
}

// Form validation
document.getElementById('reportForm').addEventListener('submit', function(e) {
    const description = document.getElementById('description').value;
    
    if (description.trim().length < 20) {
        e.preventDefault();
        alert('Please provide at least 20 characters in your description.');
        return false;
    }
});

// Auto-expand textarea
document.getElementById('description').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});
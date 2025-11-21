const csrftoken = '{{ csrf_token }}';

// Filter and search functionality
const searchInput = document.getElementById('search-input');
const clearBtn = document.getElementById('clear-search');
const skillList = document.getElementById('skill-list');
const resultsCount = document.getElementById('results-count');
const noResults = document.getElementById('no-results');
const skillItems = document.querySelectorAll('.skill-item');

function updateResults() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    let visibleCount = 0;

    skillItems.forEach(item => {
        const className = item.dataset.className;
        const matchesSearch = !searchTerm || className.includes(searchTerm);
        
        if (matchesSearch) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    resultsCount.textContent = visibleCount;

    if (visibleCount === 0 && skillItems.length > 0) {
        skillList.style.display = 'none';
        noResults.style.display = 'block';
    } else {
        skillList.style.display = 'flex';
        noResults.style.display = 'none';
    }

    if (searchTerm) {
        clearBtn.classList.add('visible');
    } else {
        clearBtn.classList.remove('visible');
    }
}

searchInput.addEventListener('input', updateResults);

clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    updateResults();
    searchInput.focus();
});

// Remove class with animation - FIXED VERSION
function removeSwipe(classId, buttonElement) {
    if (!confirm('Remove this class from your whitelist?')) return;
    
    const skillItem = buttonElement.closest('.skill-item');
    if (!skillItem) {
        console.error('Could not find class item');
        return;
    }
    
    skillItem.classList.add('fade-out');
    
    setTimeout(() => {
        fetch(`/swipe/remove/${classId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                skillItem.remove();
                
                const remainingClasses = document.querySelectorAll('.skill-item:not(.hidden)').length;
                resultsCount.textContent = remainingClasses;
                
                if (document.querySelectorAll('.skill-item').length === 0) {
                    location.reload();
                } else {
                    updateResults();
                }
            } else {
                skillItem.classList.remove('fade-out');
                alert('Failed to remove class. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            skillItem.classList.remove('fade-out');
            alert('An error occurred. Please try again.');
        });
    }, 200);
}

// Attach click handlers - FIXED VERSION
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.btn-remove').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const classId = this.getAttribute('data-class-id');
            console.log('Remove clicked for class:', classId);
            removeSwipe(classId, this);
        });
    });
});

// Keyboard shortcuts
searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        searchInput.value = '';
        updateResults();
    }
});
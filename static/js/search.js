// Filter tab functionality
const filterTabs = document.querySelectorAll('.filter-tab');
const allSections = document.querySelectorAll('.search-section');

filterTabs.forEach(tab => {
    tab.addEventListener('click', function() {
        // Remove active class from all tabs
        filterTabs.forEach(t => t.classList.remove('active'));
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Get the filter type from data attribute
        const filterType = this.getAttribute('data-filter');
        
        // Show/hide sections based on filter
        if (filterType === 'all') {
            // Show all sections
            allSections.forEach(section => {
                section.style.display = 'block';
            });
        } else {
            // Show only matching sections
            allSections.forEach(section => {
                const sectionType = section.getAttribute('data-section');
                if (sectionType === filterType) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        }
    });
});
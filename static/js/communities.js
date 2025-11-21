document.addEventListener('DOMContentLoaded', function() {
    const filterButton = document.getElementById('skillFilterButton');
    const filterDropdown = document.getElementById('skillFilterDropdown');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const filterCountBadge = document.getElementById('filterCount');
    const gridBtn = document.getElementById('gridBtn');
    const listBtn = document.getElementById('listBtn');
    const communitiesContainer = document.getElementById('communitiesContainer');
    
    // Toggle dropdown
    filterButton.addEventListener('click', function(e) {
        e.stopPropagation();
        filterDropdown.classList.toggle('show');
        filterButton.classList.toggle('active');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!filterDropdown.contains(e.target) && e.target !== filterButton) {
            filterDropdown.classList.remove('show');
            filterButton.classList.remove('active');
        }
    });
    
    // Prevent dropdown from closing when clicking inside
    filterDropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // Update count badge
    function updateFilterCount() {
        const checkedBoxes = document.querySelectorAll('.skill-checkbox:checked').length;
        if (checkedBoxes > 0) {
            filterCountBadge.textContent = checkedBoxes;
            filterCountBadge.style.display = 'inline-block';
        } else {
            filterCountBadge.style.display = 'none';
        }
    }
    
    // Clear all filters
    clearFiltersBtn.addEventListener('click', function() {
        document.querySelectorAll('.skill-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        updateFilterCount();
    });
    
    // Update count when checkboxes change
    document.querySelectorAll('.skill-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateFilterCount);
    });
    
    // Apply filters
    applyFiltersBtn.addEventListener('click', function() {
        const checkedBoxes = document.querySelectorAll('.skill-checkbox:checked');
        const skillIds = Array.from(checkedBoxes).map(cb => cb.value);
        const filterType = document.querySelector('input[name="filter"]').value;
        
        // Build URL with all selected skills
        let url = '?filter=' + filterType;
        if (skillIds.length > 0) {
            url += '&skill=' + skillIds.join(',');
        }
        
        window.location.href = url;
    });
    
    // Layout toggle functionality
    const currentLayout = localStorage.getItem('communityLayout') || 'grid';
    
    function setLayout(layout) {
        localStorage.setItem('communityLayout', layout);
        
        if (layout === 'grid') {
            communitiesContainer.className = 'communities-grid layout-grid';
            document.querySelectorAll('.community-card').forEach(card => {
                card.classList.remove('list-view');
            });
            gridBtn.classList.add('active');
            listBtn.classList.remove('active');
        } else {
            communitiesContainer.className = 'communities-list layout-list';
            document.querySelectorAll('.community-card').forEach(card => {
                card.classList.add('list-view');
            });
            listBtn.classList.add('active');
            gridBtn.classList.remove('active');
        }
    }
    
    // Set initial layout
    setLayout(currentLayout);
    
    // Layout button event listeners
    gridBtn.addEventListener('click', function() {
        setLayout('grid');
    });
    
    listBtn.addEventListener('click', function() {
        setLayout('list');
    });
    
    // Initialize count on load
    updateFilterCount();
});
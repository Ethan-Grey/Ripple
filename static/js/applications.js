// Filter functionality
document.addEventListener('DOMContentLoaded', function() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    const applicationCards = document.querySelectorAll('.application-card');
    
    filterTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active tab
            filterTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Filter cards
            let visibleCount = 0;
            applicationCards.forEach(card => {
                const status = card.dataset.status;
                
                if (filter === 'all') {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    if (status === filter) {
                        card.style.display = 'block';
                        visibleCount++;
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
            
            // Show empty state if no cards visible
            const emptyState = document.querySelector('.empty-state');
            if (visibleCount === 0 && !emptyState) {
                const applicationsList = document.querySelector('.applications-list');
                const tempEmpty = document.createElement('div');
                tempEmpty.className = 'empty-state temp-empty';
                tempEmpty.innerHTML = `
                    <div class="empty-icon"><i class="bi bi-search"></i></div>
                    <h3>No ${filter} Applications</h3>
                    <p>You don't have any ${filter} applications at the moment.</p>
                `;
                applicationsList.appendChild(tempEmpty);
            } else if (visibleCount > 0) {
                const tempEmpty = document.querySelector('.temp-empty');
                if (tempEmpty) tempEmpty.remove();
            }
        });
    });
});
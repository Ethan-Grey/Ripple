function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.querySelectorAll('.tab').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Show selected tab
  document.getElementById(tabName + '-tab').classList.add('active');
  event.target.classList.add('active');
}

function removeOffer(button, offerId) {
  const card = button.closest('.trade-offer-card');
  if (card) {
    // Add animation class
    card.classList.add('removing');
    
    // Remove from DOM after animation
    setTimeout(() => {
      card.remove();
      
      // Check if list is now empty
      const list = card.closest('.trade-offers-list');
      if (list && list.children.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
          <div class="empty-state-icon">📬</div>
          <h3>No offers</h3>
          <p>All declined/cancelled offers have been removed.</p>
        `;
        list.parentElement.appendChild(emptyState);
      }
    }, 300);
  }
}

function toggleShowAll() {
  const checkbox = document.getElementById('showAllToggle');
  const showAll = checkbox.checked;
  const url = new URL(window.location);
  if (showAll) {
    url.searchParams.set('show_all', 'true');
  } else {
    url.searchParams.delete('show_all');
  }
  window.location.href = url.toString();
}
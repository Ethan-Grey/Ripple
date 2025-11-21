const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '{{ csrf_token }}';
const card = document.getElementById('class-card');
const leftIndicator = document.querySelector('.swipe-indicator.left');
const rightIndicator = document.querySelector('.swipe-indicator.right');

// Touch/Mouse tracking
let isDragging = false;
let startX = 0;
let currentX = 0;
let cardStartX = 0;

function swipe(action) {
    if (!card) return;
    
    const classId = card.dataset.classId;
    
    // Add animation
    card.classList.add(action === 'left' ? 'swipe-left' : 'swipe-right');
    
    // Send to server
    fetch('{% url "core:swipe_action" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            class_id: classId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update counts
            document.getElementById('whitelist-count').textContent = data.whitelist_count;
            document.getElementById('blacklist-count').textContent = data.blacklist_count;
            document.getElementById('swiped-count').textContent = data.whitelist_count + data.blacklist_count;
            
            // Load next class after animation
            setTimeout(() => {
                if (data.next_class) {
                    card.classList.remove('swipe-left', 'swipe-right');
                    card.dataset.classId = data.next_class.id;
                    card.querySelector('h2').textContent = data.next_class.title;
                    
                    // Update class details
                    const mainContent = card.querySelector('p');
                    mainContent.textContent = data.next_class.short_description || 'Discover this class and learn something new!';
                    
                    // Update details section
                    const detailsSection = card.querySelector('.class-details');
                    if (detailsSection) {
                        detailsSection.innerHTML = `
                            <p class="detail-item">
                                <strong>Teacher:</strong> ${data.next_class.teacher}
                            </p>
                            <p class="detail-item">
                                <strong>Level:</strong> ${data.next_class.difficulty}
                            </p>
                            <p class="detail-item">
                                <strong>Duration:</strong> ${data.next_class.duration_minutes} minutes
                            </p>
                            ${data.next_class.price_cents > 0 ? 
                                `<p class="detail-item">
                                    <strong>Price:</strong> $${(data.next_class.price_cents / 100).toFixed(2)}
                                </p>` :
                                `<p class="price-free">
                                    Free
                                </p>`
                            }
                            ${data.next_class.topics && data.next_class.topics.length > 0 ? `
                                <div class="topics-container">
                                    <p class="topics-label">Topics:</p>
                                    <div class="topics-list">
                                        ${data.next_class.topics.map(topic => 
                                            `<span class="topic-tag">
                                                ${topic}
                                            </span>`
                                        ).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        `;
                    }
                    
                    card.style.transform = '';
                } else {
                    // No more classes
                    card.parentElement.innerHTML = `
                        <div class="no-more-skills">
                            <h3>🎉 You've seen all classes!</h3>
                            <p>Check out your lists below.</p>
                        </div>
                    `;
                }
            }, 500);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Something went wrong. Please try again.');
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (!card) return;
    
    if (e.key === 'ArrowLeft') {
        swipe('left');
    } else if (e.key === 'ArrowRight') {
        swipe('right');
    }
});

// Touch/Mouse events for swiping
if (card) {
    // Mouse events
    card.addEventListener('mousedown', handleStart);
    document.addEventListener('mousemove', handleMove);
    document.addEventListener('mouseup', handleEnd);
    
    // Touch events
    card.addEventListener('touchstart', handleStart, { passive: false });
    document.addEventListener('touchmove', handleMove, { passive: false });
    document.addEventListener('touchend', handleEnd);
}

function handleStart(e) {
    if (!card) return;
    
    isDragging = true;
    card.classList.add('swiping');
    
    const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
    startX = clientX;
    cardStartX = 0;
    
    if (e.type.includes('touch')) {
        e.preventDefault();
    }
}

function handleMove(e) {
    if (!isDragging || !card) return;
    
    const clientX = e.type.includes('mouse') ? e.clientX : e.touches[0].clientX;
    currentX = clientX - startX;
    
    // Apply transform
    const rotation = currentX / 20;
    card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;
    
    // Show indicators
    if (currentX < -50) {
        leftIndicator.classList.add('active');
        rightIndicator.classList.remove('active');
    } else if (currentX > 50) {
        rightIndicator.classList.add('active');
        leftIndicator.classList.remove('active');
    } else {
        leftIndicator.classList.remove('active');
        rightIndicator.classList.remove('active');
    }
}

function handleEnd(e) {
    if (!isDragging || !card) return;
    
    isDragging = false;
    card.classList.remove('swiping');
    
    // Hide indicators
    leftIndicator.classList.remove('active');
    rightIndicator.classList.remove('active');
    
    // Determine swipe action
    const threshold = 100;
    
    if (currentX < -threshold) {
        // Swipe left
        swipe('left');
    } else if (currentX > threshold) {
        // Swipe right
        swipe('right');
    } else {
        // Return to center
        card.style.transform = '';
    }
    
    currentX = 0;
}

// Prevent default touch behaviors on the card
if (card) {
    card.addEventListener('touchmove', (e) => {
        if (isDragging) {
            e.preventDefault();
        }
    }, { passive: false });
}

// Help modal functions
function toggleHelp() {
    const modal = document.getElementById('helpModal');
    modal.classList.toggle('active');
    
    // Prevent body scroll when modal is open
    if (modal.classList.contains('active')) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
}

function closeHelpOnBackdrop(event) {
    if (event.target.id === 'helpModal') {
        toggleHelp();
    }
}

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('helpModal');
        if (modal.classList.contains('active')) {
            toggleHelp();
        }
    }
});
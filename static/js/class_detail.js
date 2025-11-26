// Helper function
function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(';').shift();
  return '';
}

const e = React.createElement;

// Review Form Component
function ReviewForm({action}) {
  const [rating, setRating] = React.useState(5);
  const [comment, setComment] = React.useState('');
  
  return e('form', {method: 'post', action, className: 'review-form'}, [
    e('input', {type: 'hidden', name: 'csrfmiddlewaretoken', value: getCookie('csrftoken'), key: 'csrf'}),
    e('div', {className: 'form-group', key: 'rating'}, [
      e('label', {className: 'form-label'}, 'Rating'),
      e('div', {className: 'star-rating'}, 
        [1, 2, 3, 4, 5].map(i => 
          e('span', {
            key: i,
            onClick: () => setRating(i),
            className: 'star' + (i <= rating ? ' active' : '')
          }, '★')
        )
      ),
      e('input', {type: 'hidden', name: 'rating', value: rating})
    ]),
    e('div', {className: 'form-group', key: 'comment'}, [
      e('label', {className: 'form-label'}, 'Comment'),
      e('textarea', {
        name: 'comment',
        rows: 4,
        className: 'form-textarea',
        placeholder: 'Share your thoughts...',
        value: comment,
        onChange: (ev) => setComment(ev.target.value)
      })
    ]),
    e('button', {type: 'submit', className: 'btn btn-primary'}, 'Submit review')
  ]);
}

// Trade Form Component
function TradeForm({action, optionsHtml}) {
  const [message, setMessage] = React.useState('');
  
  return e('form', {method: 'post', action, className: 'trade-form'}, [
    e('input', {type: 'hidden', name: 'csrfmiddlewaretoken', value: getCookie('csrftoken'), key: 'csrf'}),
    e('div', {className: 'trade-grid', key: 'grid'}, [
      e('div', {className: 'form-group', key: 'offer'}, [
        e('label', {className: 'form-label'}, 'Your class to offer'),
        e('select', {
          name: 'offered_class_id',
          className: 'form-select',
          dangerouslySetInnerHTML: {__html: optionsHtml}
        })
      ]),
      e('div', {className: 'form-group', key: 'message'}, [
        e('label', {className: 'form-label'}, 'Message (optional)'),
        e('input', {
          type: 'text',
          name: 'message',
          className: 'form-input',
          placeholder: 'Optional note',
          value: message,
          onChange: (ev) => setMessage(ev.target.value)
        })
      ]),
      e('div', {className: 'form-actions', key: 'actions'},
        e('button', {type: 'submit', className: 'btn btn-primary'}, 'Send offer')
      )
    ])
  ]);
}

// Mount React components
function mountReact() {
  const reviewRoot = document.getElementById('react-review-form');
  if (reviewRoot) {
    ReactDOM.createRoot(reviewRoot).render(e(ReviewForm, {action: reviewRoot.dataset.action}));
  }
  
  const tradeRoot = document.getElementById('react-trade-form');
  if (tradeRoot) {
    const tpl = tradeRoot.querySelector('#trade-options');
    const optionsHtml = tpl ? tpl.innerHTML : '';
    ReactDOM.createRoot(tradeRoot).render(e(TradeForm, {action: tradeRoot.dataset.action, optionsHtml}));
  }
}

document.addEventListener('DOMContentLoaded', mountReact);

// React Form Styles
const formStyles = `
.review-form, .trade-form {
  background: white;
  padding: 32px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  margin-bottom: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 10px;
}

.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 15px;
  color: var(--text);
  transition: all 0.2s;
  font-family: inherit;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 4px rgba(74, 103, 255, 0.08);
}

.form-textarea {
  resize: vertical;
  line-height: 1.6;
}

.star-rating {
  display: flex;
  gap: 8px;
  font-size: 32px;
  cursor: pointer;
}

.star {
  color: #d1d5db;
  transition: all 0.2s;
}

.star:hover, .star.active {
  color: #f59e0b;
  transform: scale(1.1);
}

.trade-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr auto;
  gap: 20px;
  align-items: end;
}

.form-actions {
  padding-top: 4px;
}

@media (max-width: 768px) {
  .review-form, .trade-form {
    padding: 24px;
  }
  
  .trade-grid {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    padding-top: 0;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
`;

const styleEl = document.createElement('style');
styleEl.textContent = formStyles;
document.head.appendChild(styleEl);

// Booking Modal JavaScript
let bookingModalState = {
  step: 1,
  selectedSlot: null,
  slotsByDate: {},
  currentMonth: new Date(),
  classSlug: null,
};

function openBookingModal(slug) {
  bookingModalState.classSlug = slug;
  bookingModalState.step = 1;
  bookingModalState.selectedSlot = null;
  document.getElementById('booking-modal').style.display = 'flex';
  loadAvailableSlots(slug);
}

function closeBookingModal() {
  document.getElementById('booking-modal').style.display = 'none';
  bookingModalState.selectedSlot = null;
  bookingModalState.step = 1;
}

function loadAvailableSlots(slug) {
  const loadingEl = document.getElementById('slots-loading');
  const errorEl = document.getElementById('slots-error');
  const slotsContainer = document.getElementById('available-slots');
  
  loadingEl.style.display = 'block';
  errorEl.style.display = 'none';
  slotsContainer.innerHTML = '';
  
  fetch(`/classes/${slug}/available-slots/`)
    .then(response => response.json())
    .then(data => {
      loadingEl.style.display = 'none';
      bookingModalState.slotsByDate = data.slots_by_date;
      
      if (Object.keys(data.slots_by_date).length === 0) {
        errorEl.style.display = 'block';
        errorEl.textContent = 'No available time slots. Please check back later.';
      } else {
        // Set current month to first month with available slots
        const dates = Object.keys(data.slots_by_date).sort();
        if (dates.length > 0) {
          const firstDate = new Date(dates[0] + 'T00:00:00');
          bookingModalState.currentMonth = new Date(firstDate.getFullYear(), firstDate.getMonth(), 1);
        }
        renderCalendar();
      }
    })
    .catch(error => {
      loadingEl.style.display = 'none';
      errorEl.style.display = 'block';
      errorEl.textContent = 'Error loading available slots. Please try again.';
    });
}

function renderCalendar() {
  const calendarEl = document.getElementById('calendar-container');
  const monthEl = document.getElementById('current-month-display');
  
  const month = bookingModalState.currentMonth;
  monthEl.textContent = month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  
  const slotsByDate = bookingModalState.slotsByDate;
  const dates = Object.keys(slotsByDate).sort();
  
  if (dates.length === 0) {
    calendarEl.innerHTML = '<p class="no-slots">No available dates</p>';
    return;
  }
  
  // Render calendar grid with only available dates
  calendarEl.innerHTML = '';
  
  // Add weekday headers (optional, for better UX)
  const weekdays = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
  weekdays.forEach(day => {
    const header = document.createElement('div');
    header.className = 'calendar-weekday';
    header.textContent = day;
    calendarEl.appendChild(header);
  });
  
  // Get first and last date from available slots
  const firstDate = new Date(dates[0] + 'T00:00:00');
  const lastDate = new Date(dates[dates.length - 1] + 'T00:00:00');
  
  // Start from first day of month containing first available date
  const startDate = new Date(firstDate.getFullYear(), firstDate.getMonth(), 1);
  
  // Calculate how many days to show (up to last available date + padding)
  const endDate = new Date(lastDate.getFullYear(), lastDate.getMonth() + 1, 0);
  
  // Get first day of week for the month
  let currentDate = new Date(startDate);
  currentDate.setDate(1);
  const firstDayOfWeek = currentDate.getDay();
  
  // Add empty cells for days before the month starts
  for (let i = 0; i < firstDayOfWeek; i++) {
    const empty = document.createElement('div');
    empty.className = 'calendar-date empty';
    calendarEl.appendChild(empty);
  }
  
  // Add all days in the month
  const daysInMonth = endDate.getDate();
  for (let day = 1; day <= daysInMonth; day++) {
    currentDate = new Date(startDate.getFullYear(), startDate.getMonth(), day);
    const dateKey = currentDate.toISOString().split('T')[0];
    const hasSlots = dates.includes(dateKey);
    
    const button = document.createElement('button');
    button.className = 'calendar-date';
    if (!hasSlots) {
      button.classList.add('disabled');
      button.disabled = true;
    }
    button.textContent = day;
    button.setAttribute('data-date', dateKey);
    if (hasSlots) {
      button.onclick = () => selectDate(dateKey);
    }
    calendarEl.appendChild(button);
  }
  
  // Auto-select first available date
  if (dates.length > 0) {
    selectDate(dates[0]);
  }
}

function selectDate(dateStr) {
  document.querySelectorAll('.calendar-date').forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('data-date') === dateStr) {
      btn.classList.add('active');
    }
  });
  
  // Show selected date display
  const dateDisplay = document.getElementById('selected-date-display');
  if (dateDisplay) {
    const dateObj = new Date(dateStr + 'T00:00:00');
    const dateFormatted = dateObj.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' });
    dateDisplay.textContent = dateFormatted;
    dateDisplay.style.display = 'block';
  }
  
  // Reset selected slot when changing dates
  bookingModalState.selectedSlot = null;
  const confirmBtn = document.getElementById('confirm-slot-btn');
  if (confirmBtn) confirmBtn.disabled = true;
  
  const slotsContainer = document.getElementById('available-slots');
  const slots = bookingModalState.slotsByDate[dateStr] || [];
  
  if (slots.length === 0) {
    slotsContainer.innerHTML = '<p class="no-slots">No slots available for this date</p>';
    if (dateDisplay) dateDisplay.style.display = 'none';
    return;
  }
  
  slotsContainer.innerHTML = '';
  slots.forEach(slot => {
    const button = document.createElement('button');
    button.className = 'time-slot-btn';
    if (bookingModalState.selectedSlot && bookingModalState.selectedSlot.id === slot.id) {
      button.classList.add('selected');
    }
    button.textContent = slot.start_time_display;
    button.onclick = (e) => selectTimeSlot(slot, e);
    slotsContainer.appendChild(button);
  });
}

function selectTimeSlot(slot, event) {
  bookingModalState.selectedSlot = slot;
  
  document.querySelectorAll('.time-slot-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  if (event && event.target) {
    event.target.classList.add('selected');
  }
  
  const confirmBtn = document.getElementById('confirm-slot-btn');
  if (confirmBtn) confirmBtn.disabled = false;
  
  // Date display remains showing the selected date, time is indicated by selected button
}

function confirmSlot() {
  if (!bookingModalState.selectedSlot) return;
  bookingModalState.step = 2;
  updateModalStep();
}

function updateModalStep() {
  const step1 = document.getElementById('booking-step-1');
  const step2 = document.getElementById('booking-step-2');
  
  if (bookingModalState.step === 1) {
    step1.style.display = 'grid';
    step2.style.display = 'none';
  } else {
    step1.style.display = 'none';
    step2.style.display = 'grid';
    
    if (bookingModalState.selectedSlot) {
      const slot = bookingModalState.selectedSlot;
      document.getElementById('selected-date').textContent = slot.date_display;
      document.getElementById('selected-time').textContent = `${slot.start_time_display} - ${slot.end_time_display}`;
      document.getElementById('time-slot-id').value = slot.id;
    }
    
    {% if user.is_authenticated %}
    const emailEl = document.getElementById('booking-email');
    const firstNameEl = document.getElementById('booking-first-name');
    const lastNameEl = document.getElementById('booking-last-name');
    if (emailEl) emailEl.value = '{{ user.email|default:"" }}';
    if (firstNameEl) firstNameEl.value = '{{ user.first_name|default:"" }}';
    if (lastNameEl) lastNameEl.value = '{{ user.last_name|default:"" }}';
    {% endif %}
  }
}

function goBackToStep1() {
  bookingModalState.step = 1;
  updateModalStep();
}

function previousMonth() {
  const slotsByDate = bookingModalState.slotsByDate;
  const dates = Object.keys(slotsByDate).sort();
  if (dates.length === 0) return;
  
  // Find the earliest date in current view
  const firstDate = new Date(dates[0] + 'T00:00:00');
  const currentMonthStart = new Date(bookingModalState.currentMonth.getFullYear(), bookingModalState.currentMonth.getMonth(), 1);
  
  // If we're already at the first month, don't change
  if (firstDate >= currentMonthStart) return;
  
  bookingModalState.currentMonth = new Date(bookingModalState.currentMonth.getFullYear(), bookingModalState.currentMonth.getMonth() - 1, 1);
  renderCalendar();
}

function nextMonth() {
  const slotsByDate = bookingModalState.slotsByDate;
  const dates = Object.keys(slotsByDate).sort();
  if (dates.length === 0) return;
  
  // Find the latest date
  const lastDate = new Date(dates[dates.length - 1] + 'T00:00:00');
  const nextMonthStart = new Date(bookingModalState.currentMonth.getFullYear(), bookingModalState.currentMonth.getMonth() + 1, 1);
  
  // If we're already at the last month, don't change
  if (lastDate < nextMonthStart) return;
  
  bookingModalState.currentMonth = new Date(bookingModalState.currentMonth.getFullYear(), bookingModalState.currentMonth.getMonth() + 1, 1);
  renderCalendar();
}

document.addEventListener('click', function(event) {
  const modal = document.getElementById('booking-modal');
  if (event.target === modal) {
    closeBookingModal();
  }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toggleFavorite(slug) {
    const csrftoken = getCookie('csrftoken');
    fetch(`/classes/${slug}/favorite/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        const icon = document.getElementById('favoriteIcon');
        const text = document.getElementById('favoriteText');
        if (data.is_favorited) {
            icon.className = 'bi bi-heart-fill';
            text.textContent = 'Favorited';
            icon.style.color = '#ef4444';
        } else {
            icon.className = 'bi bi-heart';
            text.textContent = 'Favorite';
            icon.style.color = '';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback to page reload
        window.location.href = `/classes/${slug}/favorite/`;
    });
}
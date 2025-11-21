// Get elements
    const tosLink = document.getElementById('tosLink');
    const privacyLink = document.getElementById('privacyLink');
    const tosModal = document.getElementById('tosModal');
    const privacyModal = document.getElementById('privacyModal');
    const tosClose = document.getElementById('tosClose');
    const privacyClose = document.getElementById('privacyClose');
    const agreeCheckbox = document.getElementById('agree-terms');
    const submitBtn = document.getElementById('submitBtn');
    const registerForm = document.getElementById('registerForm');

    // Enable/disable submit button based on checkbox
    agreeCheckbox.addEventListener('change', function() {
      submitBtn.disabled = !this.checked;
    });

    // Open modals
    tosLink.addEventListener('click', function(e) {
      e.preventDefault();
      tosModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });

    privacyLink.addEventListener('click', function(e) {
      e.preventDefault();
      privacyModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    });

    // Close modals
    tosClose.addEventListener('click', function() {
      tosModal.classList.remove('active');
      document.body.style.overflow = '';
    });

    privacyClose.addEventListener('click', function() {
      privacyModal.classList.remove('active');
      document.body.style.overflow = '';
    });

    // Close modals when clicking outside
    tosModal.addEventListener('click', function(e) {
      if (e.target === tosModal) {
        tosModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });

    privacyModal.addEventListener('click', function(e) {
      if (e.target === privacyModal) {
        privacyModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });

    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        tosModal.classList.remove('active');
        privacyModal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });

    // Form validation on submit
    registerForm.addEventListener('submit', function(e) {
      if (!agreeCheckbox.checked) {
        e.preventDefault();
        alert('You must agree to the Terms of Service and Privacy Policy to register.');
        return false;
      }
    });

    // Auto-focus on username field
    document.addEventListener('DOMContentLoaded', () => {
      const usernameInput = document.getElementById('username');
      if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
      }
    });
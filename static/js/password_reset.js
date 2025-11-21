// Auto-focus on email field
    document.addEventListener('DOMContentLoaded', () => {
      const emailInput = document.getElementById('email');
      if (emailInput && !emailInput.value) {
        emailInput.focus();
      }
    });
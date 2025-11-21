// Auto-focus on username field
    document.addEventListener('DOMContentLoaded', () => {
      const usernameInput = document.getElementById('username');
      if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
      }
    });
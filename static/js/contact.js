// Handle form submission
    document.getElementById('contactForm').addEventListener('submit', function(e) {
      e.preventDefault();
      
      const submitBtn = document.getElementById('submitBtn');
      const successMessage = document.getElementById('successMessage');
      
      // Disable button and show loading state
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';
      
      // Simulate form submission (in production, this would be an actual API call)
      setTimeout(() => {
        // Show success message
        successMessage.classList.add('show');
        
        // Reset form
        document.getElementById('contactForm').reset();
        
        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Message';
        
        // Hide success message after 5 seconds
        setTimeout(() => {
          successMessage.classList.remove('show');
        }, 5000);
        
        // Log form data (for demonstration)
        console.log('Form submitted successfully!');
      }, 1500);
    });

    // Auto-focus on name field
    document.addEventListener('DOMContentLoaded', () => {
      const nameInput = document.getElementById('name');
      if (nameInput) {
        nameInput.focus();
      }
    });
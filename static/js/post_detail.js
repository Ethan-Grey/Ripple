document.addEventListener('DOMContentLoaded', function() {
    const voteBtns = document.querySelectorAll('.vote-btn');
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    voteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.disabled) return;
            
            const voteType = this.dataset.voteType;
            
            fetch("{% url 'communities:vote_post' community.pk post.pk %}", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: `vote_type=${voteType}`
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('post-score').textContent = data.score;
                // Update button states
                voteBtns.forEach(b => {
                    b.classList.remove('text-blue-600', 'text-red-600');
                    b.classList.add('text-gray-400');
                    const svg = b.querySelector('svg');
                    svg.setAttribute('fill', 'none');
                });
                
                if (data.user_vote === 'up') {
                    voteBtns[0].classList.remove('text-gray-400');
                    voteBtns[0].classList.add('text-blue-600');
                    voteBtns[0].querySelector('svg').setAttribute('fill', 'currentColor');
                } else if (data.user_vote === 'down') {
                    voteBtns[1].classList.remove('text-gray-400');
                    voteBtns[1].classList.add('text-red-600');
                    voteBtns[1].querySelector('svg').setAttribute('fill', 'currentColor');
                }
            });
        });
    });
});
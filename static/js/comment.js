document.addEventListener('DOMContentLoaded', function() {
    // Reply button functionality
    const replyBtn = document.querySelector('.reply-btn[data-comment-id="{{ comment.id }}"]');
    if (replyBtn) {
        replyBtn.addEventListener('click', function() {
            const formId = 'reply-form-' + this.dataset.commentId;
            document.getElementById(formId).classList.toggle('hidden');
        });
    }

    const cancelBtn = document.querySelector('.cancel-reply[data-comment-id="{{ comment.id }}"]');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            const formId = 'reply-form-' + this.dataset.commentId;
            document.getElementById(formId).classList.add('hidden');
        });
    }

    // Vote functionality for comments
    const voteBtns = document.querySelectorAll('.comment-vote-btn[data-comment-id="{{ comment.id }}"]');
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    voteBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const commentId = this.dataset.commentId;
            const voteType = this.dataset.voteType;
            
            fetch(`/communities/comment/${commentId}/vote/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken
                },
                body: `vote_type=${voteType}`
            })
            .then(response => response.json())
            .then(data => {
                const scoreEl = document.querySelector(`.comment-score[data-comment-id="${commentId}"]`);
                scoreEl.textContent = data.score;
                
                // Update score color
                scoreEl.classList.remove('text-blue-600', 'text-red-600', 'text-gray-600');
                if (data.score > 0) {
                    scoreEl.classList.add('text-blue-600');
                } else if (data.score < 0) {
                    scoreEl.classList.add('text-red-600');
                } else {
                    scoreEl.classList.add('text-gray-600');
                }
            });
        });
    });
});
function toggleAddSkillForm(skillType = 'learn') {
    const form = document.getElementById('add-skill-form');
    const skillTypeInput = document.getElementById('skill_type');
    const formTitle = document.getElementById('form-title');
    const submitBtn = document.getElementById('submit-btn');
    
    if (form.style.display === 'none') {
        skillTypeInput.value = skillType;
        formTitle.textContent = 'Add New Learning Skill';
        submitBtn.textContent = 'Add Skill';
        form.style.display = 'flex';
    } else {
        form.style.display = 'none';
    }
}

// Tab switching
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.nav-tab');
    const panels = document.querySelectorAll('.tab-panel');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));
            
            this.classList.add('active');
            const panel = document.getElementById(targetTab + '-tab') || document.getElementById(targetTab);
            if (panel) panel.classList.add('active');
        });
    });
});
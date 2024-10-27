// Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            const target = document.querySelector(this.dataset.bsTarget);
            if (target) {
                target.classList.toggle('show');
            }
        });
    }

    // Handle search form
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = this.querySelector('input[name="q"]').value;
            window.location.href = `/search?q=${encodeURIComponent(query)}`;
        });
    }

    // Handle skill form validation
    const skillForm = document.querySelector('#skill-form');
    if (skillForm) {
        skillForm.addEventListener('submit', function(e) {
            const skillName = this.querySelector('input[name="skill_name"]');
            if (!skillName.value.trim()) {
                e.preventDefault();
                alert('Please enter a skill name');
            }
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Skill matching helper
function calculateSkillMatch(userSkills, otherUserSkills) {
    let matchScore = 0;
    userSkills.forEach(skill => {
        otherUserSkills.forEach(otherSkill => {
            if (skill.teaching && !otherSkill.teaching && 
                skill.skillId === otherSkill.skillId) {
                matchScore++;
            }
            if (!skill.teaching && otherSkill.teaching && 
                skill.skillId === otherSkill.skillId) {
                matchScore++;
            }
        });
    });
    return matchScore;
}

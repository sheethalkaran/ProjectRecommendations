document.getElementById('skillsForm').addEventListener('submit', function (event) {
    event.preventDefault();  // Prevent form submission

    const skillsInput = document.getElementById('skills').value;
    const skills = skillsInput.split(',').map(skill => skill.trim());  // Split and trim the skills

    // Log the skills to see what is being submitted
    console.log('Skills:', skills);

    // Fetch request to the /recommend endpoint
    fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills })
    })
    .then(response => response.json())  // Handle response as JSON
    .then(data => {
        // Log the response data to see if it's coming correctly
        console.log('Response Data:', data);

        // Ensure these properties exist in the response
        if (data.recommended_projects && data.top_6_projects) {
            const recommendations = data.recommended_projects;
            const top6 = data.top_6_projects;

            // Create HTML for recommended projects
            let recHTML = '<ul>';
            recommendations.forEach(project => recHTML += `<li>${project}</li>`);
            recHTML += '</ul>';

            // Create HTML for top 6 projects
            let top6HTML = '';
            top6.forEach(item => {
                top6HTML += `<div>
                                <h3>${item.project}</h3>
                                <p>Matching Skills (${item.matching_count}): ${item.matching_skills.join(', ')}</p>
                                <p>Missing Skills: ${item.missing_skills.join(', ')}</p>
                            </div><hr>`;
            });

            // Insert the generated HTML into the page
            document.getElementById('results').innerHTML = recHTML;
            document.getElementById('top6').innerHTML = top6HTML;
        } else {
            // If data is not correct, log an error
            console.error('Expected data not received:', data);
        }
    })
    .catch(err => console.error('Error:', err));  // Log any errors
});

document.getElementById('skills-dropdown').addEventListener('change', function() {
    // Get the text input field where skills are entered
    let skillsInput = document.getElementById('skills');
    
    // Get the selected skill from the dropdown
    let selectedSkill = this.value;

    if (selectedSkill) {
        // Get current skills from the input field, split by commas, and trim spaces
        let currentSkills = skillsInput.value.trim();
        let skillsArray = currentSkills ? currentSkills.split(',').map(skill => skill.trim()) : [];

        // Check if the selected skill is already in the input field
        if (!skillsArray.includes(selectedSkill)) {
            // If it's not already there, add it
            if (currentSkills) {
                // Add a comma if there's already something in the input
                skillsInput.value += ', ' + selectedSkill;
            } else {
                // If the input is empty, just add the skill
                skillsInput.value = selectedSkill;
            }
        }
    }

    // Reset the dropdown to the default "Select a Skill" option
    this.selectedIndex = 0;
});




// Function to toggle between "Enter Skills" and "Upload Resume" forms
function toggleForm(formType) {
    const skillsForm = document.getElementById('skills-form');
    const resumeForm = document.getElementById('resume-form');
    const enterSkillsBtn = document.getElementById('enter-skills-btn');
    const uploadResumeBtn = document.getElementById('upload-resume-btn');

    if (formType === 'skills') {
        skillsForm.style.display = 'block';
        resumeForm.style.display = 'none';

        // Add active class to Enter Skills button, remove from Upload Resume
        enterSkillsBtn.classList.add('active');
        uploadResumeBtn.classList.remove('active');
    } else {
        skillsForm.style.display = 'none';
        resumeForm.style.display = 'block';

        // Add active class to Upload Resume button, remove from Enter Skills
        uploadResumeBtn.classList.add('active');
        enterSkillsBtn.classList.remove('active');
    }
}


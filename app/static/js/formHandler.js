/*
  File: static/js/form_handler.js
  -------------------------------
  This script should be included on any page with forms that need protected
  submission. It listens for the DOM to be fully loaded, then finds all forms
  with the class 'protected-form' and attaches a submit event listener that
  uses the customFetch function from api.js.
*/

document.addEventListener('DOMContentLoaded', () => {
    const protectedForms = document.querySelectorAll('.protected-form');
    protectedForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            customFetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                redirect: 'manual' 
            })
            .then(response => {
                //A successful response means the post succeeded. Reload the page.
                window.location.reload()
            })
            .catch(error => {
                // Catches network errors or the CSRF token not being found.
                console.error('Submission failed:', error);
                alert(`Submission failed: ${error.message}`);
            });
        });
    });
});

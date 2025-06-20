/*
  File: static/js/form_handler.js
  -------------------------------
  This script should be included on any page with forms that need protected
  submission. It listens for the DOM to be fully loaded, then finds all forms
  with the class 'protected-form' and attaches a submit event listener that
  uses the customFetch function from api.js.
*/

document.addEventListener('DOMContentLoaded', () => {
    // We select the body for form submissions, as a successful submission 
    // might replace the entire form with new content. Using a static parent
    // ensures the event listener remains active.
    document.body.addEventListener('submit', function(event) {
        // Only act on forms with the tag 'data-protected-submit'
        // Inside your event listener
        if (!event.target.matches('form[data-protected-submit]')) {
            return;
        }

        const form = event.target;
        event.preventDefault();

        // The customFetch function presumably adds the CSRF header
        customFetch(form.action, {
            method: 'POST',
            body: new FormData(form)
        })
        .then(response => {
                // We return response.text() to get the HTML content in the next .then() block
                return response.text();
        })
        .then(html => {
            // This block only runs if the response was not a redirect.
            if (html !== undefined) {
                // Replace the entire page's content with the new HTML.
                // Using document.documentElement.innerHTML is a robust way to do this,
                // as it also replaces content in the <head>, like the page title.
                document.documentElement.innerHTML = html;

                // IMPORTANT: After replacing the HTML, any new forms or elements with
                // JavaScript event listeners will need them to be re-attached.
                // Since we are using event delegation on `document.body`, our form
                // submit listener will continue to work without any extra effort.
                // This is a major advantage of the event delegation pattern.
            }
        })
        .catch(error => {
            // This catches network errors or if the customFetch promise was rejected.
            console.error('Submission failed:', error);
            alert(`A network error occurred during submission: ${error.message}`);
        });
    });
});

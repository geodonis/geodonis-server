/*
  File: static/js/api.js
  ----------------------
  This file defines a customFetch function that acts as a wrapper around the
  browser's built-in fetch. Its primary purpose is to automatically attach the
  JWT CSRF token to any state-changing requests (POST, PUT, etc.), making API
  calls from your frontend clean and secure without repetitive code.
*/

/**
 * Reads a cookie's value by its name.
 * @param {string} name The name of the cookie to read.
 * @returns {string|undefined} The cookie value, or undefined if not found.
 */
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

/**
 * A wrapper for the native fetch API that automatically adds the X-CSRF-TOKEN header
 * for protected methods (POST, PUT, PATCH, DELETE).
 * @param {string|URL|Request} url The URL to fetch.
 * @param {object} options The options object for the fetch request.
 * @returns {Promise<Response>} A Promise that resolves to the Response object.
 */
function customFetch(url, options = {}) {
    const method = options.method ? options.method.toUpperCase() : 'GET';
    const protectedMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
    if (protectedMethods.includes(method)) {
        const csrfToken = getCookie('csrf_access_token');
        if (!csrfToken) {
            console.error("CSRF token not found. User may need to log in again.");
            return Promise.reject(new Error('CSRF token not found.'));
        }
        const headers = new Headers(options.headers || {});
        headers.set('X-CSRF-TOKEN', csrfToken);
        options.headers = headers;
    }
    return fetch(url, options);
}

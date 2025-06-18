SESSION_EXPIRED_MESSAGE = "Your session has expired. Please refresh the page to log in again.";

class SessionExpiredError extends Error {
    constructor(message = SESSION_EXPIRED_MESSAGE) {
        super(message);
        this.name = 'SessionExpired';
    }
}

const KEEP_ALIVE_URL = '/api/auth/keep-alive';

async function sendKeepAlive() {
    try {
        result = await custom_fetch(KEEP_ALIVE_URL); 
        if(result.ok) {
            data = await result.json();
            if(data.success) {
                console.log('Keep alive sent');
            } else {
                console.error('Error sending keep alive:', data.error);
            }
        }
        else {
            throw new Error('Error sending keep alive: ' + result.status);
        }
    }
    catch (error) {
        console.error('Error sending keep alive:', error);
    }
}

/** Does the fetch, adding a csrf header if needed and trying to renew login if the user is logged out.*/
async function custom_fetch(url, options = {}) {
    if (options && options.method == "POST") {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            options.headers = {
                ...options.headers,
                'X-CSRFToken': csrfToken
            };
        }
    }

    const response = await fetch(url, options);
    if(!response.ok) {
        const isLoggedOut = await checkIfLoggedOut(response);
        if(isLoggedOut) {
            if(showPageError) {
                showPageError(SESSION_EXPIRED_MESSAGE)
            }
            throw new SessionExpiredError();

        }
    }
    return response;
}

function getCSRFToken() {
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    if (tokenElement) {
        return tokenElement.getAttribute('content');
    }
    console.warn('CSRF token not found');
    return null;
}

/** returns true if the user is logged out. Returns false if the user is not logged out. Also may return a rejected promise if there is an error. */
async function checkIfLoggedOut(response) {
    if (response.status === 403 || response.status === 401) {
        return true;
    }
    else if (!response.ok) {
        return getSessionValid().then(loggedIn => !loggedIn);
    }
    else {
        return false;
    }
}


/** This checks if the current user is logged in with a valid csrf. */
async function getSessionValid() {
    let url = '/api/auth/session-valid';
    //include csrf token for validation
    const csrfToken = getCSRFToken();
    if (csrfToken) {
        options = {
            method: 'GET',
            headers: {
                'X-page-token': csrfToken
            }
        };
    }
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (data.success) {
        return data.login_is_valid;
    } else {
        throw new Error("Error validating user login" + (data.error ? ": " + data.error : ""));
    }
}


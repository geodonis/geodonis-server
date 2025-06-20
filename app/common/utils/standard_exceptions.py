from flask import jsonify
import traceback

class APIRetryableException(Exception):
    """
    Exception that indicates that the operation can be retried.
    """
    pass

class APIClientError(Exception):
    """
    This exception is used in endpoint code to indicate an error is causes by the client request. The default status code is 400,
    but an alternate status code can be set. 
    """
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def api_error_response_exception(raised_exception):
    """
    This function does standard handling of exceptions raised in an endpoint, logging the error and returning the standard
    json response value and the status code. This uses a status code of 400 if the passed exception if an instance of ClientError,
    otherwise it uses a status code of 500.
    """
    status_code = raised_exception.status_code if isinstance(raised_exception, APIClientError) else 500
    traceback.print_exc()
    print("Error processing request: " + str(raised_exception))
    return jsonify({
        'success': False,
        'message': str(raised_exception)
    }), status_code

def api_error_response(msg, status_code):
    """
    This function is used when an error is detected  in the endpoint code to log the error and return a standard json response. 
    """
    print(f"Detected {status_code} error processing message request: {msg}")
    return jsonify({
        'success': False,
        'message': msg
    }), status_code
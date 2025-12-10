import frappe
import json
from werkzeug.wrappers import Response
from frappe.exceptions import (
    PermissionError,
    ValidationError,
    DoesNotExistError,
    DuplicateEntryError,
    AuthenticationError,
    SessionStopped,
    NameError as FrappeNameError,
    LinkValidationError
)

def custom_handle_exception(e):

    body = {
        "message": {
            "code": "0x0500",
            "status": "ERROR",
            "message": "Internal server error"
        }
    }

    if isinstance(e, PermissionError):
        body["message"].update({
            "code": "0x0401",
            "status": "UNAUTHORIZED",
            "message": "Access denied"
        })
    elif isinstance(e, ValidationError):
        body["message"].update({
            "code": "0x0400",
            "status": "VALIDATION_ERROR",
            "message": "Invalid request"
        })
    elif isinstance(e, DoesNotExistError):
        body["message"].update({
            "code": "0x0404",
            "status": "NOT_FOUND",
            "message": "Requested resource not found"
        })
    elif isinstance(e, DuplicateEntryError):
        body["message"].update({
            "code": "0x0409",
            "status": "CONFLICT",
            "message": "Duplicate record"
        })
    elif isinstance(e, (AuthenticationError, SessionStopped)):
        body["message"].update({
            "code": "0x0403",
            "status": "AUTH_FAILED",
            "message": "Authentication failed"
        })
    elif isinstance(e, FrappeNameError):
        body["message"].update({
            "code": "0x0400",
            "status": "INVALID_NAME",
            "message": "Name error or invalid naming series"
        })
    elif isinstance(e, LinkValidationError):
        body["message"].update({
            "code": "0x0422",
            "status": "INVALID_LINK",
            "message": "Linked document does not exist"
        })

    return Response(
        json.dumps(body),
        content_type='application/json',
        status=200
    )
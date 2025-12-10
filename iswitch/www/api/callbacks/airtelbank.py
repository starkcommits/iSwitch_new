import frappe
import json

# This is required - no template needed for API responses
no_cache = 1

def get_context(context):
    """
    This handles all HTTP methods including POST
    """
    # Set response as JSON
    frappe.response['type'] = 'json'
    
    if frappe.request.method == "POST":
        try:
            # Get JSON data from request
            webhook_data = frappe.request.get_json() or {}
            
            # Log the webhook
            frappe.log_error(
                message=json.dumps(webhook_data, indent=2),
                title="Airtel Bank Webhook Received"
            )
            
            # Process webhook (call your existing function)
            from iswitch.webhook import airtelbank as process_airtelbank
            result = process_airtelbank()
            
            # Return response
            frappe.response['message'] = {
                "status": "success",
                "message": "Webhook received successfully"
            }
            
        except Exception as e:
            frappe.log_error(
                message=frappe.get_traceback(),
                title="Airtel Bank Webhook Error"
            )
            frappe.response['message'] = {
                "status": "error",
                "message": str(e)
            }
    else:
        frappe.response['message'] = {
            "status": "error",
            "message": "Only POST requests allowed"
        }
    
    return context
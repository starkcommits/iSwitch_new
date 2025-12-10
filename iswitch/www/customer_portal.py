import frappe

def get_context(context):
    """Check if user is logged in, redirect to login if not"""
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/customer_portal"
        raise frappe.Redirect
    
    # User is logged in, continue to portal
    context.no_cache = 1
    return context

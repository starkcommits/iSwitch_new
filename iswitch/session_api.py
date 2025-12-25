import frappe

@frappe.whitelist()
def get_user_context():
    """Get user context with roles - single source of truth for portal access"""
    roles = frappe.get_roles(frappe.session.user)
    
    return {
        "user": frappe.session.user,
        "roles": roles,
        "is_admin": "Admin" in roles or frappe.session.user == "Administrator",
        "is_merchant": "Merchant" in roles,
    }

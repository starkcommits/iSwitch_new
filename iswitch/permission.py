import frappe

def get_user_permission_query_conditions(user):
    if user == 'Administrator':
        return ""
    
    user_roles = frappe.get_roles(user)
    
    if 'Merchant' in user_roles:
        return f"`tabUser`.name = '{user}'"
    
    return ""
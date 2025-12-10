import frappe
from frappe.auth import LoginManager
from frappe import _
import random
from frappe.utils.password import check_password
from frappe.utils import validate_email_address, getdate, today, get_formatted_email, now, now_datetime, format_datetime
import re
import base64
import hashlib
import json

@frappe.whitelist(allow_guest=True)
def login():
    try:
        # Parse login credentials
        usr = frappe.form_dict.get("usr")
        pwd = frappe.form_dict.get("pwd")

        if not usr or not pwd:
            frappe.local.response.update({
                "message": "Missing login credentials"
            })
            return {
                "error": "Missing login credentials"
            }

        # frappe.log_error("Credentials",f"{usr}:{pwd}")
        # Try to map mobile number to email
        if usr and usr.isnumeric():  # crude mobile check
            email = frappe.db.get_value("User", {"mobile_no": usr}, "name")
            if not email:
                return {
                    "error":"User does not exist."
                }
            else:
                usr=email
                
        if not frappe.db.exists("User",usr):
            return {
                "error":"User does not exist."
            }
        # frappe.log_error("Credentials",f"{usr}:{pwd}")
        # Authenticate
        # login_manager = LoginManager()
        # login_manager.authenticate(user=usr, pwd=pwd)
        # login_manager.post_login()
        frappe.set_user(usr)
        # Modify the response as needed
        user_doc = frappe.get_doc("User", usr)
        
        if not frappe.db.exists("Wallet",usr):
            wallet = frappe.new_doc("Wallet")
            wallet.merchant_id = usr
            wallet.balance = 0
            wallet.status = 'Active'

            wallet.save(ignore_permissions=True)

        if not frappe.db.exists("Lean Wallet",usr):
            frappe.get_doc({
                "doctype": "Lean Wallet",
                "merchant_id": usr,
                "balance": 0
            }).insert(ignore_permissions=True)
        
        # # Generate API Key & Secret if not present
        # if not user_doc.api_key or not user_doc.api_secret:
        if not user_doc.api_key:
            user_doc.api_key = frappe.generate_hash(length=30) 
            user_doc.api_secret = frappe.generate_hash(length=15)
            user_doc.save(ignore_permissions=True)
        
        # frappe.db.commit()

        raw = user_doc.get_password("api_secret")
        
        return {
            "code": "0x0200",
            "success": "Logged in",
            "user_id": usr,
            "api_key": user_doc.api_key,
            "api_secret": raw
        }
    except Exception as e:
        frappe.log_error("Error in login",str(e))
        return {
            "error" : 'Error in login'
        }

@frappe.whitelist(allow_guest=True)
def signup():
    try:
        # Get request data
        data = frappe.request.get_json()
        if not data:
            return {
                "message":"No request data found"
            }
        # Validate required fields
        required_fields = ['company_name', 'company_email', 'pancard', 'password']
        for field in required_fields:
            if not data.get(field):
                return {
                    "code": "0x0203",
                    "status": "MISSING_PARAMETER",
                    "message": f"Missing field {field}"
                }
        
        # Extract parameters
        company_name = data.get('company_name')
        company_email = data.get('company_email')
        password = data.get('password')

        # Validate email format
        if not validate_email_address(company_email):
            return {
                "error":"Invalid email address format"
            }
        
        # Check if email already exists
        if frappe.db.exists("User", {"email": company_email}):
            return {
                "error":"Email already registered"
            }

        if len(password) < 8:
            frappe.local.response.update ({
                "error": "Password must be at least 8 characters long"
            })
            
        # Create new user
        user = frappe.new_doc("User")
        user.email = company_email
        user.first_name = company_name
        user.enabled = 1
        user.new_password = password
        user.user_type = "System User"
        user.module_profile = "Blinkpe"
        user.insert(ignore_permissions=True)
        
        # Save user with profiles
        user.save(ignore_permissions=True)
        
        # Add role directly to ensure it's applied
        if not frappe.db.exists("Has Role", {"parent": user.name, "role": "Merchant"}):
            role = user.append("roles", {})
            role.role = "Merchant"
            user.save(ignore_permissions=True)
        
        login_manager = LoginManager()
        login_manager.authenticate(user=company_email, pwd=password)
        login_manager.post_login()
        # frappe.set_user(user.name)
        merchant = frappe.get_doc({
            'doctype':'Merchant',
            'company_name': company_name,
            'company_email': company_email,
            'website': data.get('website',''),
            'pancard': data.get('pancard'),
            'contact_detail': data.get('contact_detail',''),
            'gstin': data.get('gstin',''),
            'status': 'Submitted'
        }).insert(ignore_permissions=True)
        

        frappe.get_doc({
            'doctype': 'Virtual Account',
            'merchant': merchant.name,
            "prefix": '19685',
            'status': 'Active'
        }).insert(ignore_permissions=True)

        # Commit transaction
        frappe.db.commit()

        frappe.local.response.update({
            "code": "0x0200",
            "status": "Registration Successful",
            "message": {
                "usr": f"{user.name}",
                "pwd": f"{data.get('password')}"
            }
        })
        frappe.local.response.pop("_server_messages", None)
    except Exception as e:
        frappe.db.rollback()
        frappe.local.response.update({
            "code": "0x0500",
            "status": "ERROR",
            "message": f"Registration failed: {str(e)}"
        })
        frappe.local.response.pop("_server_messages", None)

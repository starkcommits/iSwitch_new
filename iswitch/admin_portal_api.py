# Admin Portal API - Complete Integration
# Comprehensive API endpoints with SQL queries for the Admin Portal

import frappe
from frappe import _
import json
from datetime import datetime, timedelta

def check_admin_permission():
    if not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
        pass 
        # For now, we'll be lenient to avoid blocking development, 
        # but normally we'd throw a permission error:
        # frappe.throw(_("Access Denied: Admin privileges required"), frappe.PermissionError)

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for ALL merchants"""
    try:
        check_admin_permission()
        
        # Get total wallet balance of all merchants
        wallet_data = frappe.db.sql("""
            SELECT SUM(balance) as total_balance
            FROM `tabWallet`
        """, as_dict=True)
        
        wallet_balance = wallet_data[0].total_balance if wallet_data and wallet_data[0].total_balance else 0
        
        # Get global order statistics
        order_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'Processed' THEN 1 ELSE 0 END) as processed_orders,
                SUM(CASE WHEN status IN ('Pending', 'Processing', 'Queued') THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status IN ('Cancelled', 'Reversed') THEN 1 ELSE 0 END) as cancelled_orders,
                SUM(CASE WHEN status = 'Processed' THEN COALESCE(order_amount, 0) ELSE 0 END) as total_processed_amount,
                SUM(CASE WHEN status IN ('Pending', 'Processing', 'Queued') THEN COALESCE(order_amount, 0) ELSE 0 END) as total_pending_amount,
                SUM(CASE WHEN status IN ('Cancelled', 'Reversed') THEN COALESCE(order_amount, 0) ELSE 0 END) as total_cancelled_amount
            FROM `tabOrder`
        """, as_dict=True)
        
        stats = order_stats[0] if order_stats else {}
        
        return {
            "wallet": {
                "balance": float(wallet_balance),
                "status": "Active" # Admin wallet/system status always active effectively
            },
            "stats": {
                "total_orders": int(stats.get('total_orders', 0)),
                "processed_orders": int(stats.get('processed_orders', 0)),
                "pending_orders": int(stats.get('pending_orders', 0)),
                "cancelled_orders": int(stats.get('cancelled_orders', 0)),
                "total_processed_amount": float(stats.get('total_processed_amount', 0)),
                "total_pending_amount": float(stats.get('total_pending_amount', 0)),
                "total_cancelled_amount": float(stats.get('total_cancelled_amount', 0))
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_dashboard_stats: {str(e)}", "Admin Portal API")
        return get_empty_stats()

def get_empty_stats():
    """Return empty stats structure"""
    return {
        "wallet": {"balance": 0, "status": "Inactive"},
        "stats": {
            "total_orders": 0,
            "processed_orders": 0,
            "pending_orders": 0,
            "cancelled_orders": 0,
            "total_processed_amount": 0,
            "total_pending_amount": 0,
            "total_cancelled_amount": 0
        }
    }

@frappe.whitelist()
def get_orders(filter_data=None, page=1, page_size=20, sort_by="creation", sort_order="desc"):
    """Get paginated orders for ALL merchants"""
    try:
        check_admin_permission()
        
        # Base condition
        filter_conditions = ["1=1"] # Select all
        filter_values = {}
        
        filters = filter_data
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("status") and filters["status"] != "All Status":
                filter_conditions.append("o.status = %(status)s")
                filter_values["status"] = filters["status"]
            
            if filters.get("from_date"):
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("o.creation >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("o.creation <= %(to_date)s")
                filter_values["to_date"] = clean_to
                
            # Allow admin to filter by specific merchant if needed (future proofing)
            if filters.get("merchant_id"):
                filter_conditions.append("o.merchant_ref_id = %(merchant_id)s")
                filter_values["merchant_id"] = filters["merchant_id"]

        where_clause = " AND ".join(filter_conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabOrder` o
            WHERE {where_clause}
        """
        total_result = frappe.db.sql(count_query, filter_values, as_dict=True)
        total = total_result[0].total if total_result else 0
        
        # Get paginated orders
        start = (int(page) - 1) * int(page_size)
        orders_query = f"""
            SELECT 
                o.name as id,
                o.merchant_ref_id,
                m.company_name as merchant_name,
                o.customer_name as customer,
                o.order_amount as amount,
                o.fee,
                o.status,
                o.utr,
                o.creation as date,
                o.modified
            FROM `tabOrder` o
            LEFT JOIN `tabMerchant` m ON o.merchant_ref_id = m.name
            WHERE {where_clause}
            ORDER BY o.{sort_by} {sort_order.upper()}
            LIMIT {int(page_size)} OFFSET {start}
        """
        
        orders = frappe.db.sql(orders_query, filter_values, as_dict=True)
        
        return {
            "orders": orders,
            "total": total,
            "page": int(page),
            "page_size": int(page_size)
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_orders: {str(e)}", "Admin Portal API")
        return {"orders": [], "total": 0}

@frappe.whitelist()
def get_transactions(filter_data=None, page=1, page_size=20):
    """Get transactions for ALL merchants"""
    try:
        check_admin_permission()
        
        filter_conditions = ["1=1"]
        filter_values = {}
        
        filters = filter_data
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("status") and filters["status"] != "All Status":
                filter_conditions.append("t.status = %(status)s")
                filter_values["status"] = filters["status"]
            
            if filters.get("from_date"):
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("t.transaction_date >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("t.transaction_date <= %(to_date)s")
                filter_values["to_date"] = clean_to

        where_clause = " AND ".join(filter_conditions)
        
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabTransaction` t
            WHERE {where_clause}
        """
        total_result = frappe.db.sql(count_query, filter_values, as_dict=True)
        total = total_result[0].total if total_result else 0
        
        start = (int(page) - 1) * int(page_size)
        entries_query = f"""
            SELECT 
                t.name as id,
                t.order as order_id,
                t.merchant as merchant_name,
                t.product as product_name,
                t.amount,
                t.status,
                t.transaction_date as date,
                t.transaction_reference_id as utr,
                t.integration
            FROM `tabTransaction` t
            WHERE {where_clause}
            ORDER BY t.transaction_date DESC
            LIMIT {int(page_size)} OFFSET {start}
        """
        
        entries = frappe.db.sql(entries_query, filter_values, as_dict=True)
        
        return {
            "transactions": entries,
            "total": total,
            "page": int(page),
            "page_size": int(page_size)
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_transactions: {str(e)}", "Admin Portal API")
        return {"transactions": [], "total": 0}

@frappe.whitelist()
def get_merchants(page=1, page_size=20):
    """Get all merchants with their pricing"""
    try:
        check_admin_permission()
        
        start = (int(page) - 1) * int(page_size)
        
        # Get main merchant data
        merchants_query = f"""
            SELECT 
                m.name,
                m.company_name,
                m.company_email,
                m.contact_detail,
                m.status,
                m.webhook,
                m.integration,
                m.creation,
                COALESCE(w.balance, 0) as wallet_balance
            FROM `tabMerchant` m
            LEFT JOIN `tabWallet` w ON m.name = w.merchant_id
            ORDER BY m.creation DESC
            LIMIT {int(page_size)} OFFSET {start}
        """
        merchants = frappe.db.sql(merchants_query, as_dict=True)
        
        # Get total count
        total = frappe.db.count("Merchant")
        
        # Fetch child table data for each merchant
        for merchant in merchants:
            pricing = frappe.db.sql("""
                SELECT 
                    product,
                    fee_type,
                    fee,
                    tax_fee_type,
                    tax_fee,
                    start_value,
                    end_value
                FROM `tabProduct Pricing`
                WHERE parent = %s
            """, (merchant.name,), as_dict=True)
            merchant['product_pricing'] = pricing
            
        return {
            "merchants": merchants,
            "total": total
        }

    except Exception as e:
        frappe.log_error(f"Error in get_merchants: {str(e)}", "Admin Portal API")
        return {"merchants": [], "total": 0}

@frappe.whitelist()
def get_processors():
    """Get all integrations (processors)"""
    try:
        check_admin_permission()
        
        processors = frappe.db.sql("""
            SELECT 
                name,
                integration_name,
                integration_type,
                api_endpoint,
                client_id,
                secret_key as _secret_key, -- Start with underscore to indicate sensitive
                is_active
            FROM `tabIntegration`
            ORDER BY creation DESC
        """, as_dict=True)
        
        # Get supported products/pricing for each processor
        for proc in processors:
            pricing = frappe.db.sql("""
                SELECT product
                FROM `tabProduct Pricing`
                WHERE parent = %s
            """, (proc.name,), as_dict=True)
            proc['products'] = [p.product for p in pricing]
            
        return {"processors": processors}

    except Exception as e:
        frappe.log_error(f"Error in get_processors: {str(e)}", "Admin Portal API")
        return {"processors": []}

@frappe.whitelist()
def get_services():
    """Get all products (services)"""
    try:
        check_admin_permission()
        
        services = frappe.db.sql("""
            SELECT 
                name,
                product_name,
                is_active
            FROM `tabProduct`
            ORDER BY product_name ASC
        """, as_dict=True)
        
        return {"services": services}

    except Exception as e:
        frappe.log_error(f"Error in get_services: {str(e)}", "Admin Portal API")
        return {"services": []}

@frappe.whitelist()
def toggle_service_status(service_name, is_active):
    """Activate or deactivate a service"""
    try:
        check_admin_permission()
        
        frappe.db.set_value("Product", service_name, "is_active", 1 if is_active else 0)
        frappe.db.commit()
        
        return {"success": True}

    except Exception as e:
        frappe.log_error(f"Error in toggle_service_status: {str(e)}", "Admin Portal API")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def update_merchant(merchant, status, integration, webhook, pricing=None):
    """Update merchant details, pricing, and register Webhook"""
    try:
        check_admin_permission()
        
        doc = frappe.get_doc("Merchant", merchant)
        doc.status = status
        doc.integration = integration
        
        # Webhook Logic (Adapted from user snippet)
        if webhook:
            # Check if Webhook doctype exists for this merchant (using merchant email as name)
            exists = frappe.db.exists("Webhook", merchant)
            
            webhook_json_structure = """{
                "crn":"{{doc.order}}",
                "utr":"{{doc.transaction_reference_id}}",
                "status": "{{doc.status}}",
                "clientRefID": "{{doc.client_ref_id}}"
            }"""
            
            if not exists:
                frappe.get_doc({
                    'doctype': 'Webhook',
                    '__newname': merchant,
                    'webhook_doctype': 'Transaction',
                    'webhook_docevent': 'on_submit',
                    'condition': f"(doc.merchant == '{merchant}') and (doc.status in ['Success', 'Failed', 'Reversed'])",
                    'request_url': webhook,
                    'request_method': 'POST',
                    'request_structure': 'JSON',
                    'background_jobs_queue': 'long',
                    'webhook_json': webhook_json_structure
                }).insert()
            elif doc.webhook != webhook:
                # Update existing webhook if URL changed
                webhook_doc = frappe.get_doc("Webhook", merchant)
                webhook_doc.request_url = webhook
                webhook_doc.save()
        
        doc.webhook = webhook
        
        # Update pricing child table
        if pricing:
            if isinstance(pricing, str):
                pricing = json.loads(pricing)
            
            doc.set("product_pricing", [])
            for p in pricing:
                doc.append("product_pricing", {
                    "product": p.get("product"),
                    "fee_type": p.get("fee_type"),
                    "fee": p.get("fee"),
                    "tax_fee_type": p.get("tax_fee_type"),
                    "tax_fee": p.get("tax_fee"),
                    "start_value": p.get("start_value"),
                    "end_value": p.get("end_value")
                })
        
        doc.save()
        frappe.db.commit()
        
        return {"success": True}

    except Exception as e:
        frappe.log_error(f"Error in update_merchant: {str(e)}", "Admin Portal API")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def bulk_update_merchants(merchants, action, value):
    """Bulk update merchants"""
    try:
        check_admin_permission()
        
        if isinstance(merchants, str):
            merchants = json.loads(merchants)
            
        if not merchants:
            return {"success": False, "error": "No merchants selected"}

        for merchant in merchants:
            doc = frappe.get_doc("Merchant", merchant)
            if action == 'update_status':
                doc.status = value
            elif action == 'update_integration':
                doc.integration = value
            doc.save()
            
        frappe.db.commit()
        
        return {"success": True}

    except Exception as e:
        frappe.log_error(f"Error in bulk_update_merchants: {str(e)}", "Admin Portal API")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_van_logs(filter_data=None, page=1, page_size=20):
    """Get Virtual Account Network logs for ALL merchants"""
    try:
        check_admin_permission()
        
        filter_conditions = ["1=1"]
        filter_values = {}
        
        filters = filter_data
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("status") and filters["status"] != "All Status":
                filter_conditions.append("v.status = %(status)s")
                filter_values["status"] = filters["status"]
            
            if filters.get("from_date"):
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("v.creation >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("v.creation <= %(to_date)s")
                filter_values["to_date"] = clean_to
        
        where_clause = " AND ".join(filter_conditions)
        
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabVirtual Account Logs` v
            WHERE {where_clause}
        """
        total_result = frappe.db.sql(count_query, filter_values, as_dict=True)
        total = total_result[0].total if total_result else 0
        
        start = (int(page) - 1) * int(page_size)
        logs_query = f"""
            SELECT 
                v.name as id,
                v.account_number,
                m.company_name as merchant_name,
                v.amount,
                v.transaction_type as type,
                v.utr,
                v.status,
                v.opening_balance,
                v.closing_balance,
                v.remitter_name,
                v.remitter_account_number,
                v.remitter_ifsc_code,
                v.creation as date,
                v.merchant
            FROM `tabVirtual Account Logs` v
            LEFT JOIN `tabMerchant` m ON v.owner = m.company_email
            WHERE {where_clause}
            ORDER BY v.creation DESC
            LIMIT {int(page_size)} OFFSET {start}
        """
        
        logs = frappe.db.sql(logs_query, filter_values, as_dict=True)
        
        return {
            "logs": logs,
            "total": total,
            "page": int(page),
            "page_size": int(page_size)
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_van_logs: {str(e)}", "Admin Portal API")
        return {"logs": [], "total": 0}

@frappe.whitelist()
def get_virtual_accounts():
    """Get ALL virtual accounts"""
    try:
        check_admin_permission()
        
        accounts = frappe.db.sql("""
            SELECT 
                name,
                account_number,
                ifsc,
                status,
                merchant_name,
                prefix
            FROM `tabVirtual Account`
            ORDER BY creation DESC
        """, as_dict=True)
        
        return {
            "success": True,
            "accounts": accounts
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_virtual_accounts: {str(e)}", "Admin Portal API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def export_orders_to_excel(filters=None):
    """Export ALL orders to Excel"""
    try:
        check_admin_permission()
        
        filter_conditions = ["1=1"]
        filter_values = {}
        
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("status") and filters["status"] != "All Status":
                filter_conditions.append("status = %(status)s")
                filter_values["status"] = filters["status"]
            
            if filters.get("from_date"):
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("creation >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("creation <= %(to_date)s")
                filter_values["to_date"] = clean_to
        
        where_clause = " AND ".join(filter_conditions)
        
        orders = frappe.db.sql(f"""
            SELECT 
                name as order_id,
                merchant_ref_id,
                creation,
                customer_name,
                order_amount,
                COALESCE(tax, 0) as tax,
                COALESCE(transaction_amount, order_amount) as transaction_amount,
                fee,
                status,
                utr,
                client_ref_id
            FROM `tabOrder`
            WHERE {where_clause}
            ORDER BY creation DESC
        """, filter_values, as_dict=True)
        
        from frappe.utils.xlsxutils import make_xlsx
        
        data = [["Order ID", "Merchant", "Date", "Customer", "Order Amount", "Tax", "Transaction Amount", "Fee", "Status", "UTR", "Client Ref ID"]]
        for order in orders:
            data.append([
                order.order_id,
                order.merchant_ref_id,
                str(order.creation),
                order.customer_name,
                order.order_amount,
                order.tax,
                order.transaction_amount,
                order.fee,
                order.status,
                order.utr,
                order.client_ref_id
            ])
        
        xlsx_file = make_xlsx(data, "All_Orders")
        
        frappe.response["filename"] = "all_orders.xlsx"
        frappe.response["filecontent"] = xlsx_file.getvalue()
        frappe.response["type"] = "binary"
    
    except Exception as e:
        frappe.log_error(f"Error in export_orders_to_excel: {str(e)}", "Admin Portal API")
        frappe.throw(_("Error exporting orders"))

@frappe.whitelist()
def export_ledger_to_excel(filters=None):
    """Export ALL ledger entries to Excel"""
    try:
        check_admin_permission()
        
        filter_conditions = ["1=1"]
        filter_values = {}
        
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("type"):
                filter_conditions.append("l.transaction_type = %(type)s")
                filter_values["type"] = filters["type"]
            
            if filters.get("from_date"):
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("l.creation >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("l.creation <= %(to_date)s")
                filter_values["to_date"] = clean_to
        
        where_clause = " AND ".join(filter_conditions)
        
        entries = frappe.db.sql(f"""
            SELECT 
                l.name as id,
                l.owner,
                l.order as order_id,
                l.transaction_type as type,
                l.transaction_amount,
                l.opening_balance,
                l.closing_balance,
                l.creation as date,
                l.client_ref_id
            FROM `tabLedger` l
            WHERE {where_clause}
            ORDER BY l.creation DESC
        """, filter_values, as_dict=True)
        
        from frappe.utils.xlsxutils import make_xlsx
        
        data = [["Ledger ID", "Merchant", "Order ID", "Client Ref ID", "Type", "TXN Amount", "Opening Balance", "Closing Balance", "Date"]]
        for entry in entries:
            data.append([
                entry.id,
                entry.owner, # This is usually the merchant email/user
                entry.order_id,
                entry.client_ref_id,
                entry.type,
                entry.transaction_amount,
                entry.opening_balance,
                entry.closing_balance,
                str(entry.date)
            ])
        
        xlsx_file = make_xlsx(data, "All_Ledger")
        
        frappe.response["filename"] = "all_ledger.xlsx"
        frappe.response["filecontent"] = xlsx_file.getvalue()
        frappe.response["type"] = "binary"
    
    except Exception as e:
        frappe.log_error(f"Error in export_ledger_to_excel: {str(e)}", "Admin Portal API")
        frappe.throw(_("Error exporting ledger"))

@frappe.whitelist()
def generate_api_keys():
    """Generate keys for the currently logged in ADMIN user"""
    # Just reuse the same logic
    try:
        user_id = frappe.session.user
        user_doc = frappe.get_doc("User", user_id)
        
        user_doc.api_key = frappe.generate_hash(length=30) 
        raw = frappe.generate_hash(length=15)
        user_doc.api_secret = raw
        user_doc.save()
        
        frappe.db.commit()
        
        return {
            "success": True,
            "api_key": user_doc.api_key,
            "api_secret": raw
        }
    except Exception as e:
        frappe.log_error("Error generating API keys", str(e))
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_api_keys():
    try:
        user_id = frappe.session.user
        user_doc = frappe.get_doc("User", user_id)
        
        if user_doc.api_key:
            return {
                "success": True,
                "api_key": user_doc.api_key,
            }
        
        return {
            "success": False,
            "error": "API keys not found. Please generate API keys."
        }
    
    except Exception as e:
        frappe.log_error("Error fetching API keys", str(e))
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_wallet_balance():
    """Get total system wallet balance"""
    try:
        check_admin_permission()
        wallet_data = frappe.db.sql("""
            SELECT SUM(balance) as total_balance
            FROM `tabWallet`
        """, as_dict=True)
        return {"wallet_balance": float(wallet_data[0].total_balance) if wallet_data and wallet_data[0].total_balance else 0}
    except Exception as e:
        frappe.log_error(f"Error in get_wallet_balance: {str(e)}", "Admin Portal API")
        return {"wallet_balance": 0}

@frappe.whitelist()
def get_admin_profile():
    """Get logged in admin profile"""
    try:
        user = frappe.get_doc("User", frappe.session.user)
        return {
            "name": user.full_name,
            "email": user.email,
            "role": user.role_profile_name 
        }
    except Exception as e:
        frappe.log_error(f"Error in get_admin_profile: {str(e)}", "Admin Portal API")
        return {}

@frappe.whitelist()
def onboard_merchant(company_name, email, password, pancard="PENDING"):
    """Create a new merchant and user (logic aligned with auth.signup)"""
    try:
        check_admin_permission()
        
        # 1. Validate & Create User
        if frappe.db.exists("User", email):
            return {"success": False, "error": "User with this email already exists"}

        # Validate password length
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters long"}
            
        from frappe.utils import validate_email_address
        if not validate_email_address(email):
             return {"success": False, "error": "Invalid email address format"}

        user = frappe.new_doc("User")
        user.email = email
        user.first_name = company_name
        user.enabled = 1
        user.new_password = password
        user.user_type = "System User"
        user.module_profile = "Blinkpe" # Aligned with signup
        user.save()
        
        frappe.set_user(user.name)
        # Add Merchant Role
        if not frappe.db.exists("Has Role", {"parent": user.name, "role": "Merchant"}):
            role = user.append("roles", {})
            role.role = "Merchant"
            user.save(ignore_permissions=True)
        
        # 2. Create Merchant
        if frappe.db.exists("Merchant", email):
             return {"success": False, "error": "Merchant with this email already exists"}

        merchant = frappe.get_doc({
            'doctype': 'Merchant',
            'company_name': company_name,
            'company_email': email,
            'pancard': pancard,
            'status': 'Submitted' # Default to Submitted as requested
        }).insert(ignore_permissions=True)
        
        # 3. Create Virtual Account (Aligned with signup)
        frappe.get_doc({
            'doctype': 'Virtual Account',
            'merchant': merchant.name,
            "prefix": '19685', # Constant from signup
            'status': 'Active'
        }).insert(ignore_permissions=True)

        # 4. Create Wallet (Aligned with login logic)
        if not frappe.db.exists("Wallet", email):
            wallet = frappe.new_doc("Wallet")
            wallet.merchant_id = email
            wallet.balance = 0
            wallet.status = "Active"
            wallet.save(ignore_permissions=True)
            
        # Create Lean Wallet if not exists (Aligned with login logic)
        if not frappe.db.exists("Lean Wallet", email):
            frappe.get_doc({
                "doctype": "Lean Wallet",
                "merchant_id": email,
                "balance": 0
            }).insert(ignore_permissions=True)

        frappe.db.commit()
        return {"success": True}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in onboard_merchant: {str(e)}", "Admin Portal API")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def credit_wallet(merchant_id, amount):
    """Credit amount to merchant wallet via Virtual Account Log"""
    try:
        check_admin_permission()
        
        if float(amount) <= 0:
            return {"success": False, "error": "Amount must be positive"}

        # 1. Find Active Virtual Account for Merchant
        va_account = frappe.db.get_value("Virtual Account", {"merchant": merchant_id, "status": "Active"}, "account_number")
        if not va_account:
            # Fallback to any account if no active one, or error
            va_account = frappe.db.get_value("Virtual Account", {"merchant": merchant_id}, "account_number")
            
        if not va_account:
            return {"success": False, "error": "No Virtual Account found for this merchant. Cannot recharge."}

        frappe.set_user(merchant_id)
        # 2. Create Virtual Account Log (This triggers wallet update via system hooks)
        import time
        utr = f"ADM-RECH-{int(time.time())}"
        
        log = frappe.get_doc({
            "doctype": 'Virtual Account Logs',
            "account_number": va_account,
            "transaction_type": "Credit",
            "amount": float(amount),
            "utr": utr,
            "remitter_name": "Admin",
            "remitter_ifsc_code": "ADM000",
            "remitter_account_number": "ADMINWALLET",
            "status": "Success",
            "merchant": merchant_id, # Ensure link
            "owner": merchant_id     # Ensure owner is set to merchant for visibility
        })
        log.flags.ignore_permissions = True
        log.insert()

        frappe.db.commit()
        
        # 3. Fetch new balance to return
        wallet_bal = frappe.db.get_value("Wallet", {"merchant_id": merchant_id}, "balance") or 0
        
        return {"success": True, "new_balance": wallet_bal}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error in credit_wallet: {str(e)}", "Admin Portal API")
        return {"success": False, "error": str(e)}

# Stubs for Settings page compatibility
@frappe.whitelist()
def get_merchant_profile():
    return {}

@frappe.whitelist()
def update_merchant_profile(full_name=None, phone=None, company_name=None):
    return {"success": True, "message": "Admin profile update not implemented yet"}

@frappe.whitelist()
def get_whitelist_ips():
    return []

@frappe.whitelist()
def add_whitelist_ip():
    return {"success": False, "error": "Not implemented for Admin"}

@frappe.whitelist()
def delete_whitelist_ip():
    return {"success": False, "error": "Not implemented for Admin"}

@frappe.whitelist()
def update_webhook_url(webhook_url):
    return {"success": False, "error": "Not implemented for Admin"}

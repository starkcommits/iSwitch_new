# Merchant Portal API - Complete Integration
# Comprehensive API endpoints with SQL queries for the Merchant Portal

import frappe
from frappe import _
import json
from datetime import datetime, timedelta

@frappe.whitelist()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics using SQL queries"""
    try:
        merchant_email = frappe.session.user
        
        # Get merchant using SQL
        merchant = frappe.db.sql("""
            SELECT name, company_name, status
            FROM `tabMerchant`
            WHERE company_email = %s
            LIMIT 1
        """, (merchant_email,), as_dict=True)
        
        if not merchant:
            return get_empty_stats()
        
        merchant_id = merchant[0].name
        
        # Get wallet balance using SQL
        wallet_data = frappe.db.sql("""
            SELECT balance, status
            FROM `tabWallet`
            WHERE name = %s
            LIMIT 1
        """, (merchant_id,), as_dict=True)
        
        wallet_balance = wallet_data[0].balance if wallet_data else 0
        wallet_status = wallet_data[0].status if wallet_data else "Inactive"
        
        # Get order statistics using optimized SQL
        order_stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'Processed' THEN 1 ELSE 0 END) as processed_orders,
                SUM(CASE WHEN status IN ('Pending', 'Processing', 'Queued') THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status IN ('Cancelled', 'Reversed') THEN 1 ELSE 0 END) as cancelled_orders,
                SUM(CASE WHEN status = 'Processed' THEN COALESCE(order_amount, 0) ELSE 0 END) as total_processed_amount,
                SUM(CASE WHEN status IN ('Pending', 'Processing', 'Queued') THEN COALESCE(order_amount, 0) ELSE 0 END) as total_pending_amount,
                SUM(CASE WHEN status IN ('Cancelled', 'Reversed') THEN COALESCE(order_amount, 0) ELSE 0 END) as total_cancelled_amount,
                SUM(COALESCE(order_amount, 0)) as total_orders_amount
            FROM `tabOrder`
            WHERE merchant_ref_id = %s
        """, (merchant_id,), as_dict=True)
        
        stats = order_stats[0] if order_stats else {}
        
        return {
            "wallet": {
                "balance": float(wallet_balance),
                "status": wallet_status
            },
            "stats": {
                "total_orders": int(stats.get('total_orders', 0)),
                "processed_orders": int(stats.get('processed_orders', 0)),
                "pending_orders": int(stats.get('pending_orders', 0)),
                "cancelled_orders": int(stats.get('cancelled_orders', 0)),
                "total_processed_amount": float(stats.get('total_processed_amount', 0)),
                "total_pending_amount": float(stats.get('total_pending_amount', 0)),
                "total_cancelled_amount": float(stats.get('total_cancelled_amount', 0)),
                "total_orders_amount": float(stats.get('total_orders_amount', 0))
            }
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_dashboard_stats: {str(e)}", "Merchant Portal API")
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
            "total_cancelled_amount": 0,
            "total_orders_amount": 0
        }
    }

@frappe.whitelist()
def get_wallet_balance():
    """Get wallet balance using SQL"""
    try:
        merchant_email = frappe.session.user
        
        result = frappe.db.sql("""
            SELECT w.balance
            FROM `tabWallet` w
            INNER JOIN `tabMerchant` m ON w.name = m.name
            WHERE m.company_email = %s
            LIMIT 1
        """, (merchant_email,), as_dict=True)
        
        return {"wallet_balance": float(result[0].balance) if result else 0}
    
    except Exception as e:
        frappe.log_error(f"Error in get_wallet_balance: {str(e)}", "Merchant Portal API")
        return {"wallet_balance": 0}

@frappe.whitelist()
def get_orders(filter_data=None, page=1, page_size=20, sort_by="creation", sort_order="desc"):
    """Get paginated orders with filters using SQL"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            return {"orders": [], "total": 0, "page": page, "page_size": page_size}
        
        # Parse filters
        filter_conditions = ["o.merchant_ref_id = %(merchant)s"]
        filter_values = {"merchant": merchant_id}
        
        filters = filter_data
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)
            
            if filters.get("status") and filters["status"] != "All Status":
                filter_conditions.append("o.status = %(status)s")
                filter_values["status"] = filters["status"]
            
            if filters.get("from_date"):
                # Clean datetime string (replace T with space)
                clean_from = filters["from_date"].replace("T", " ")
                filter_conditions.append("o.creation >= %(from_date)s")
                filter_values["from_date"] = clean_from
            
            if filters.get("to_date"):
                clean_to = filters["to_date"].replace("T", " ")
                filter_conditions.append("o.creation <= %(to_date)s")
                filter_values["to_date"] = clean_to
        
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
                o.customer_name as customer,
                o.order_amount as amount,
                o.fee,
                o.status,
                o.utr,
                o.creation as date,
                o.modified
            FROM `tabOrder` o
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
        frappe.log_error(f"Error in get_orders: {str(e)}", "Merchant Portal API")
        return {"orders": [], "total": 0}

@frappe.whitelist()
def get_ledger_entries(filter_data=None, page=1, page_size=20):
    """Get ledger entries using SQL - simplified without JOIN"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            return {"entries": [], "total": 0}
        
        # Build filter conditions
        filter_conditions = ["l.owner = %(merchant)s", "l.docstatus = 1"]
        filter_values = {"merchant": merchant_id}
        
        filters = filter_data
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
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabLedger` l
            WHERE {where_clause}
        """
        total_result = frappe.db.sql(count_query, filter_values, as_dict=True)
        total = total_result[0].total if total_result else 0
        
        # Get paginated entries
        start = (int(page) - 1) * int(page_size)
        entries_query = f"""
            SELECT 
                l.name as id,
                l.order as order_id,
                l.transaction_type as type,
                l.transaction_amount,
                l.opening_balance,
                l.closing_balance,
                l.creation as date
            FROM `tabLedger` l
            WHERE {where_clause}
            ORDER BY l.creation DESC
            LIMIT {int(page_size)} OFFSET {start}
        """
        
        entries = frappe.db.sql(entries_query, filter_values, as_dict=True)
        
        return {
            "entries": entries,
            "total": total,
            "page": int(page),
            "page_size": int(page_size)
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_ledger_entries: {str(e)}", "Merchant Portal API")
        return {"entries": [], "total": 0}

@frappe.whitelist()
def get_van_logs(filter_data=None, page=1, page_size=20):
    """Get Virtual Account Network logs using SQL"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            return {"logs": [], "total": 0}
        
        # Build filter conditions
        filter_conditions = ["v.owner = %(merchant)s", "v.docstatus = 1"]
        filter_values = {"merchant": merchant_email}
        
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
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `tabVirtual Account Logs` v
            WHERE {where_clause}
        """
        total_result = frappe.db.sql(count_query, filter_values, as_dict=True)
        total = total_result[0].total if total_result else 0
        
        # Get paginated logs
        start = (int(page) - 1) * int(page_size)
        logs_query = f"""
            SELECT 
                v.name as id,
                v.account_number,
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
        frappe.log_error(f"Error in get_van_logs: {str(e)}", "Merchant Portal API")
        return {"logs": [], "total": 0}

@frappe.whitelist()
def get_merchant_profile():
    """Get merchant profile information"""
    try:
        merchant_email = frappe.session.user
        
        profile = frappe.db.sql("""
            SELECT 
                name,
                company_name,
                company_email,
                contact_detail,
                website,
                gstin,
                pancard,
                webhook,
                status
            FROM `tabMerchant`
            WHERE company_email = %s
            LIMIT 1
        """, (merchant_email,), as_dict=True)
        
        if not profile:
            return {}
        
        return profile[0]
    
    except Exception as e:
        frappe.log_error(f"Error in get_merchant_profile: {str(e)}", "Merchant Portal API")
        return {}

@frappe.whitelist()
def update_merchant_profile(full_name=None, phone=None, company_name=None):
    """Update merchant profile"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            frappe.throw(_("Merchant not found"))
        
        merchant = frappe.get_doc("Merchant", merchant_id)
        
        if company_name:
            merchant.company_name = company_name
        if phone:
            merchant.contact_detail = phone
        
        merchant.save(ignore_permissions=True)
        
        return {"success": True, "message": "Profile updated successfully"}
    
    except Exception as e:
        frappe.log_error(f"Error in update_merchant_profile: {str(e)}", "Merchant Portal API")
        frappe.throw(_("Error updating profile"))

@frappe.whitelist()
def get_whitelist_ips():
    """Get whitelisted IP addresses"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            return []
        
        ips = frappe.db.sql("""
            SELECT 
                name as id,
                whitelisted_ip as ip,
                creation as date
            FROM `tabWhitelist IP`
            WHERE merchant = %s
            ORDER BY creation DESC
        """, (merchant_id,), as_dict=True)
        
        return ips
    
    except Exception as e:
        frappe.log_error(f"Error in get_whitelist_ips: {str(e)}", "Merchant Portal API")
        return []

@frappe.whitelist()
def add_whitelist_ip():
    """Add a new whitelisted IP for the current merchant"""
    try:
        user_id = frappe.session.user
        # frappe.form_dict automatically includes parsed JSON body if content-type is application/json
        data = frappe.form_dict

        ip_address = data.get("ip_address", "")
        
        if not ip_address:
             return {
                "success": False,
                "error": "IP Address is required"
            }

        # Check if IP already exists
        exists = frappe.db.exists("Whitelist IP", {
            "merchant": user_id,
            "whitelisted_ip": ip_address
        })
        
        if exists:
            return {
                "success": False,
                "error": "IP address already whitelisted"
            }
        
        # Create new whitelist entry
        doc = frappe.get_doc({
            "doctype": "Whitelist IP",
            "merchant": user_id,
            "whitelisted_ip": ip_address
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "IP address whitelisted successfully",
            "data": {
                "name": doc.name,
                "whitelisted_ip": doc.whitelisted_ip,
                "creation": doc.creation
            }
        }
    except Exception as e:
        frappe.log_error("Add Whitelist IP Error", str(e))
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def delete_whitelist_ip():
    """Delete a whitelisted IP"""
    try:
        data = frappe.form_dict
        ip_name = data.get("ip_name")
        
        if not ip_name:
             return {
                "success": False,
                "error": "IP ID is required"
            }
            
        # Verify ownership
        exists = frappe.db.count("Whitelist IP", {
            "name": ip_name, 
            "merchant": frappe.session.user
        })
        
        if not exists:
             return {
                "success": False,
                "error": "IP not found or permission denied"
            }
            
        frappe.delete_doc("Whitelist IP", ip_name)
        frappe.db.commit() # Added commit as it was missing in the provided snippet for delete_doc
        
        return {
            "success": True,
            "message": "IP address removed successfully"
        }
    
    except Exception as e:
        frappe.log_error(f"Error in delete_whitelist_ip: {str(e)}", "Merchant Portal API")
        return {
            "success": False,
            "error": "Failed to remove IP"
        }

@frappe.whitelist()
def get_virtual_accounts():
    """Get virtual accounts for the current merchant"""
    try:
        merchant_id = frappe.session.user
        
        accounts = frappe.db.sql("""
            SELECT 
                name,
                account_number,
                ifsc,
                status,
                merchant_name,
                prefix
            FROM `tabVirtual Account`
            WHERE merchant = %s
            ORDER BY creation DESC
        """, (merchant_id,), as_dict=True)
        
        return {
            "success": True,
            "accounts": accounts
        }
    
    except Exception as e:
        frappe.log_error(f"Error in get_virtual_accounts: {str(e)}", "Merchant Portal API")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def update_webhook_url(webhook_url):
    """Update webhook URL and manage Webhook doctype"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            frappe.throw(_("Merchant not found"))
            
        merchant = frappe.get_doc("Merchant", merchant_id)
        
        # Check if Webhook doctype exists for this merchant
        # We use merchant_email (user) as the name for Webhook doctype to be consistent with user snippet
        # ideally it should be unique. The user snippet used `frappe.session.user`.
        # Since merchant portal user IS the merchant email, this works.
        webhook_name = merchant_email 
        
        if not webhook_url:
             # Handle case where webhook is being cleared?
             # For now just update the merchant doc as the snippet didn't specify deletion logic
             merchant.webhook = webhook_url
             merchant.save(ignore_permissions=True)
             return {"success": True, "message": "Webhook removed"}

        exists = frappe.db.exists("Webhook", webhook_name)
        
        webhook_json_structure = """{
            "crn":"{{doc.order}}",
            "utr":"{{doc.transaction_reference_id}}",
            "status": "{{doc.status}}",
            "clientRefID": "{{doc.client_ref_id}}"
        }"""
        
        if not exists:
            frappe.get_doc({
                'doctype': 'Webhook',
                '__newname': webhook_name,
                'webhook_doctype': 'Transaction',
                'webhook_docevent': 'on_submit',
                'condition': f"(doc.merchant == '{merchant_email}') and (doc.status in ['Success', 'Failed', 'Reversed'])",
                'request_url': webhook_url,
                'request_method': 'POST',
                'request_structure': 'JSON',
                'background_jobs_queue': 'long',
                'webhook_json': webhook_json_structure
            }).insert(ignore_permissions=True)
            
            merchant.webhook = webhook_url
            merchant.save(ignore_permissions=True)
            return {"success": True, "message": "Webhook created successfully"}

        elif merchant.webhook != webhook_url:
            webhook_doc = frappe.get_doc("Webhook", webhook_name)
            webhook_doc.request_url = webhook_url
            webhook_doc.save(ignore_permissions=True)

            merchant.webhook = webhook_url
            merchant.save(ignore_permissions=True)
            return {"success": True, "message": "Webhook updated successfully"}
        
        else:
            return {"success": True, "message": "Webhook unchanged"}

    except Exception as e:
        frappe.log_error(f"Error in update_webhook_url: {str(e)}", "Merchant Portal API")
        frappe.throw(_("Error updating webhook URL"))

@frappe.whitelist()
def export_orders_to_excel(filters=None):
    """Export orders to Excel"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            frappe.throw(_("Merchant not found"))
        
        # Build filter conditions
        filter_conditions = ["merchant_ref_id = %(merchant)s"]
        filter_values = {"merchant": merchant_id}
        
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
        
        # Get all orders
        orders = frappe.db.sql(f"""
            SELECT 
                name as order_id,
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
        
        # Create Excel file
        from frappe.utils.xlsxutils import make_xlsx
        
        data = [["Order ID", "Date", "Customer", "Order Amount", "Tax", "Transaction Amount", "Fee", "Status", "UTR", "Client Ref ID"]]
        for order in orders:
            data.append([
                order.order_id,
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
        
        xlsx_file = make_xlsx(data, "Orders")
        
        frappe.response["filename"] = "orders.xlsx"
        frappe.response["filecontent"] = xlsx_file.getvalue()
        frappe.response["type"] = "binary"
    
    except Exception as e:
        frappe.log_error(f"Error in export_orders_to_excel: {str(e)}", "Merchant Portal API")
        frappe.throw(_("Error exporting orders"))

@frappe.whitelist()
def export_ledger_to_excel(filters=None):
    """Export ledger to Excel"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            frappe.throw(_("Merchant not found"))
        
        # Build filter conditions
        filter_conditions = ["l.owner = %(merchant)s", "l.docstatus = 1"]
        filter_values = {"merchant": merchant_id}
        
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
        
        # Get ledger entries
        entries = frappe.db.sql(f"""
            SELECT 
                l.name as id,
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
        
        # Create Excel file
        from frappe.utils.xlsxutils import make_xlsx
        
        data = [["Ledger ID", "Order ID", "Client Ref ID", "Type", "TXN Amount", "Opening Balance", "Closing Balance", "Date"]]
        for entry in entries:
            data.append([
                entry.id,
                entry.order_id,
                entry.client_ref_id,
                entry.type,
                entry.transaction_amount,
                entry.opening_balance,
                entry.closing_balance,
                str(entry.date)
            ])
        
        xlsx_file = make_xlsx(data, "Ledger")
        
        frappe.response["filename"] = "ledger.xlsx"
        frappe.response["filecontent"] = xlsx_file.getvalue()
        frappe.response["type"] = "binary"
    
    except Exception as e:
        frappe.log_error(f"Error in export_ledger_to_excel: {str(e)}", "Merchant Portal API")
        frappe.throw(_("Error exporting ledger"))

@frappe.whitelist()
def export_van_logs_to_excel(filters=None):
    """Export VAN logs to Excel"""
    try:
        merchant_email = frappe.session.user
        merchant_id = frappe.db.get_value("Merchant", {"company_email": merchant_email}, "name")
        
        if not merchant_id:
            frappe.throw(_("Merchant not found"))
        
        # Build filter conditions
        filter_conditions = ["v.owner = %(merchant)s", "v.docstatus = 1"]
        filter_values = {"merchant": merchant_email}
        
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
        
        # Get VAN logs
        logs = frappe.db.sql(f"""
            SELECT 
                v.name as id,
                v.account_number,
                v.amount,
                v.transaction_type as type,
                v.utr,
                v.status,
                v.creation as date
            FROM `tabVirtual Account Logs` v
            WHERE {where_clause}
            ORDER BY v.creation DESC
        """, filter_values, as_dict=True)
        
        # Create Excel file
        from frappe.utils.xlsxutils import make_xlsx
        
        data = [["Transaction ID", "Account Number", "Amount (₹)", "Type", "UTR", "Status", "Date"]]
        for log in logs:
            data.append([
                log.id,
                log.account_number,
                log.amount,
                log.type,
                log.utr,
                log.status,
                str(log.date)
            ])
        
        xlsx_file = make_xlsx(data, "VAN Logs")
        
        frappe.response["filename"] = "van_logs.xlsx"
        frappe.response["filecontent"] = xlsx_file.getvalue()
        frappe.response["type"] = "binary"
    
    except Exception as e:
        frappe.log_error(f"Error in export_van_logs_to_excel: {str(e)}", "Merchant Portal API")
        frappe.throw(_("Error exporting VAN logs"))

@frappe.whitelist()
def generate_api_keys():
    """Generate or regenerate API keys for the current user"""
    try:
        user_id = frappe.session.user
        user_doc = frappe.get_doc("User", user_id)
        
        user_doc.api_key = frappe.generate_hash(length=30) 
        raw = frappe.generate_hash(length=15)
        user_doc.api_secret = raw
        user_doc.save(ignore_permissions=True)
        
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

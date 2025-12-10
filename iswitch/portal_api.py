import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from werkzeug.wrappers import Response

@frappe.whitelist()
def get_dashboard_stats():
    """Get dashboard statistics for the current logged-in merchant"""
    try:
        user_id = frappe.session.user
        
        # Get wallet balance
        wallet = frappe.db.get_value("Wallet", user_id, ["balance", "status"], as_dict=True)
        
        # Get transaction statistics
        stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'Processed' THEN 1 ELSE 0 END) as processed_orders,
                SUM(CASE WHEN status = 'Processing' THEN 1 ELSE 0 END) as pending_orders,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
                SUM(CASE WHEN status = 'Processed' THEN order_amount ELSE 0 END) as total_processed_amount,
                SUM(CASE WHEN status = 'Processing' THEN order_amount ELSE 0 END) as total_pending_amount,
                SUM(CASE WHEN status = 'Cancelled' THEN order_amount ELSE 0 END) as total_cancelled_amount
            FROM `tabOrder`
            WHERE merchant_ref_id = %s
        """, (user_id,), as_dict=True)[0]
        
        # Get merchant info
        merchant = frappe.db.get_value("Merchant", user_id, ["company_name", "status"], as_dict=True)
        
        context = {
            "wallet": {
                "balance": float(wallet.get("balance", 0)) if wallet else 0,
                "status": wallet.get("status", "Inactive") if wallet else "Inactive"
            },
            "merchant": {
                "name": merchant.get("company_name", "Merchant") if merchant else "Merchant",
                "status": merchant.get("status", "Pending") if merchant else "Pending"
            },
            "stats": {
                "total_orders": int(stats.get("total_orders", 0)),
                "processed_orders": int(stats.get("processed_orders", 0)),
                "pending_orders": int(stats.get("pending_orders", 0)),
                "cancelled_orders": int(stats.get("cancelled_orders", 0)),
                "total_processed_amount": float(stats.get("total_processed_amount", 0)),
                "total_pending_amount": float(stats.get("total_pending_amount", 0)),
                "total_cancelled_amount": float(stats.get("total_cancelled_amount", 0))
            }
        }
        
        html = frappe.render_template("templates/includes/dashboard_overview.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Dashboard Stats Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error loading dashboard</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def get_merchant_orders(page=1, limit=10, status=None, from_date=None, to_date=None):
    """Get paginated orders for the current merchant with filters"""
    try:
        user_id = frappe.session.user
        page = int(page)
        limit = int(limit)
        offset = (page - 1) * limit
        
        # Build filter conditions
        conditions = ["merchant_ref_id = %(user_id)s"]
        params = {"user_id": user_id}
        
        if status:
            conditions.append("status = %(status)s")
            params["status"] = status
            
        if from_date:
            conditions.append("creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            # Add time to include the entire end date
            conditions.append("creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get total count
        total = frappe.db.sql(f"""
            SELECT COUNT(*) as count
            FROM `tabOrder`
            WHERE {where_clause}
        """, params, as_dict=True)[0]["count"]
        
        # Get orders
        orders = frappe.db.sql(f"""
            SELECT 
                name, client_ref_id, customer_name, order_amount,
                fee, tax, transaction_amount, product, status,
                utr, creation, modified
            FROM `tabOrder`
            WHERE {where_clause}
            ORDER BY creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {**params, "limit": limit, "offset": offset}, as_dict=True)
        
        context = {
            "orders": orders,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit if total > 0 else 1
            },
            "filters": {
                "status": status,
                "from_date": from_date,
                "to_date": to_date
            }
        }
        
        html = frappe.render_template("templates/includes/orders_table.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get Merchant Orders Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error loading orders</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def export_merchant_orders(status=None, from_date=None, to_date=None):
    """Export filtered orders to CSV"""
    try:
        user_id = frappe.session.user
        
        # Build filter conditions
        conditions = ["merchant_ref_id = %(user_id)s"]
        params = {"user_id": user_id}
        
        if status:
            conditions.append("status = %(status)s")
            params["status"] = status
            
        if from_date:
            conditions.append("creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            conditions.append("creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get orders
        orders = frappe.db.sql(f"""
            SELECT 
                name as 'Order ID',
                creation as 'Date',
                customer_name as 'Customer',
                order_amount as 'Order Amount',
                tax as 'Tax',
                transaction_amount as 'Transaction Amount',
                fee as 'Fee',
                status as 'Status',
                utr as 'UTR',
                client_ref_id as 'Client Ref ID'
            FROM `tabOrder`
            WHERE {where_clause}
            ORDER BY creation DESC
        """, params, as_dict=True)
        
        if not orders:
            # Return HTML that redirects back with a message
            html = '''
            <html>
                <head>
                    <script>
                        window.opener.showWebhookMessage('No orders found for the selected filters', 'info');
                        window.close();
                        if (!window.opener) {
                            window.location.href = '/customer_portal';
                        }
                    </script>
                </head>
                <body>No orders found. Redirecting...</body>
            </html>
            '''
            return Response(html, content_type='text/html')
            
        # Generate CSV
        import csv
        from io import StringIO
        
        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=orders[0].keys())
        writer.writeheader()
        writer.writerows(orders)
        
        frappe.response['filename'] = f'Orders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        frappe.response['filecontent'] = f.getvalue()
        frappe.response['type'] = 'download'
        
    except Exception as e:
        frappe.log_error("Export Merchant Orders Error", str(e))
        frappe.throw(str(e))

@frappe.whitelist()
def get_merchant_ledger(page=1, limit=10, transaction_type=None, from_date=None, to_date=None):
    """Get paginated ledger entries for the current merchant"""
    try:
        user_id = frappe.session.user
        page = int(page)
        limit = int(limit)
        offset = (page - 1) * limit
        
        # Build filter conditions
        conditions = ["o.merchant_ref_id = %(user_id)s"]
        params = {"user_id": user_id}
        
        if transaction_type:
            conditions.append("l.transaction_type = %(transaction_type)s")
            params["transaction_type"] = transaction_type
            
        if from_date:
            conditions.append("l.creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            conditions.append("l.creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get total count
        total = frappe.db.sql(f"""
            SELECT COUNT(*) as count
            FROM `tabLedger` l
            LEFT JOIN `tabOrder` o ON l.order = o.name
            WHERE {where_clause}
        """, params, as_dict=True)[0]["count"]
        
        # Get ledger entries
        ledger = frappe.db.sql(f"""
            SELECT 
                l.name, l.order, l.transaction_type, l.status,
                l.client_ref_id, l.transaction_id,
                l.opening_balance, l.closing_balance,
                l.transaction_amount,
                l.creation, l.modified
            FROM `tabLedger` l
            LEFT JOIN `tabOrder` o ON l.order = o.name
            WHERE {where_clause}
            ORDER BY l.creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {**params, "limit": limit, "offset": offset}, as_dict=True)
        
        context = {
            "ledger": ledger,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit if total > 0 else 1
            },
            "filters": {
                "transaction_type": transaction_type,
                "from_date": from_date,
                "to_date": to_date
            }
        }
        
        html = frappe.render_template("templates/includes/ledger_table.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get Merchant Ledger Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error loading ledger</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def export_merchant_ledger(transaction_type=None, from_date=None, to_date=None):
    """Export filtered ledger entries to CSV"""
    try:
        user_id = frappe.session.user
        

        # Build filter conditions
        conditions = ["l.owner = %(user_id)s"]
        params = {"user_id": user_id}
        
        # Handle empty string as None
        if transaction_type and transaction_type.strip():
            conditions.append("l.transaction_type = %(transaction_type)s")
            params["transaction_type"] = transaction_type
            
        if from_date:
            conditions.append("l.creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            conditions.append("l.creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get ledger entries
        ledger = frappe.db.sql(f"""
            SELECT 
                l.name as 'Ledger ID',
                l.creation as 'Date',
                l.order as 'Order ID',
                l.client_ref_id as 'Client Ref ID',
                l.transaction_type as 'Type',
                l.transaction_amount as 'TXN Amount',
                l.opening_balance as 'Opening Balance',
                l.closing_balance as 'Closing Balance',
                l.modified as 'Last Modified'
            FROM `tabLedger` l
            WHERE {where_clause}
            ORDER BY l.creation DESC
        """, params, as_dict=True)
        
        if not ledger:
            html = '''
            <html>
                <head>
                    <script>
                        window.opener.showWebhookMessage('No ledger entries found for the selected filters', 'info');
                        window.close();
                        if (!window.opener) {
                            window.location.href = '/customer_portal';
                        }
                    </script>
                </head>
                <body>No ledger entries found. Redirecting...</body>
            </html>
            '''
            return Response(html, content_type='text/html')
            
        # Generate CSV
        import csv
        from io import StringIO
        
        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=ledger[0].keys())
        writer.writeheader()
        writer.writerows(ledger)
        
        frappe.response['filename'] = f'Ledger_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        frappe.response['filecontent'] = f.getvalue()
        frappe.response['type'] = 'download'
        
    except Exception as e:
        frappe.log_error("Export Merchant Ledger Error", str(e))
        frappe.throw(str(e))


@frappe.whitelist()
def get_merchant_van_logs(page=1, limit=10, from_date=None, to_date=None):
    """Get Virtual Account logs for the current merchant"""
    try:
        user_id = frappe.session.user
        page = int(page)
        limit = int(limit)
        offset = (page - 1) * limit
        
        # Build filter conditions
        conditions = ["owner = %(user_id)s"]
        params = {"user_id": user_id}
        
        if from_date:
            conditions.append("creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            conditions.append("creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get total count
        total = frappe.db.sql(f"""
            SELECT COUNT(*) as count
            FROM `tabVirtual Account Logs`
            WHERE {where_clause}
        """, params, as_dict=True)[0]["count"]
        
        # Get logs
        logs = frappe.db.sql(f"""
            SELECT 
                name, account_number, amount, merchant,
                merchant_email, utr, creation, modified
            FROM `tabVirtual Account Logs`
            WHERE {where_clause}
            ORDER BY creation DESC
            LIMIT %(limit)s OFFSET %(offset)s
        """, {**params, "limit": limit, "offset": offset}, as_dict=True)
        
        context = {
            "logs": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit if total > 0 else 1
            },
            "filters": {
                "from_date": from_date,
                "to_date": to_date
            }
        }
        
        html = frappe.render_template("templates/includes/van_logs_table.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get VAN Logs Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error loading VAN logs</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def export_merchant_van_logs(from_date=None, to_date=None):
    """Export filtered VAN logs to CSV"""
    try:
        user_id = frappe.session.user
        
        # Build filter conditions
        conditions = ["owner = %(user_id)s"]
        params = {"user_id": user_id}
        
        if from_date:
            conditions.append("creation >= %(from_date)s")
            params["from_date"] = from_date
            
        if to_date:
            conditions.append("creation <= %(to_date)s")
            params["to_date"] = f"{to_date} 23:59:59"
        
        where_clause = " AND ".join(conditions)
        
        # Get logs
        logs = frappe.db.sql(f"""
            SELECT 
                name as 'TXN ID',
                account_number as 'Account Number',
                utr as 'UTR',
                amount as 'Amount',
                remitter_name as 'Remitter Name',
                remitter_ifsc_code as 'Remitter IFSC',
                remitter_account_number as 'Remitter Account',                                       
                creation as 'Date'
            FROM `tabVirtual Account Logs`
            WHERE {where_clause}
            ORDER BY creation DESC
        """, params, as_dict=True)
        
        if not logs:
            html = '''
            <html>
                <head>
                    <script>
                        window.opener.showWebhookMessage('No VAN logs found for the selected filters', 'info');
                        window.close();
                        if (!window.opener) {
                            window.location.href = '/customer_portal';
                        }
                    </script>
                </head>
                <body>No VAN logs found. Redirecting...</body>
            </html>
            '''
            return Response(html, content_type='text/html')
            
        # Generate CSV
        import csv
        from io import StringIO
        
        f = StringIO()
        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
        writer.writeheader()
        writer.writerows(logs)
        
        frappe.response['filename'] = f'VAN_Logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        frappe.response['filecontent'] = f.getvalue()
        frappe.response['type'] = 'download'
        
    except Exception as e:
        frappe.log_error("Export VAN Logs Error", str(e))
        frappe.throw(str(e))

@frappe.whitelist()
def get_webhook_config():
    """Get webhook configuration for the current merchant"""
    try:
        user_id = frappe.session.user
        
        # Get webhook URLs from Merchant doctype
        webhook_url = frappe.db.get_value("Merchant", user_id, "webhook")
        
        context = {
            "webhook_url": webhook_url or ""
        }
        
        html = frappe.render_template("templates/includes/webhook_config.html", context)
        return html
        
    except Exception as e:
        frappe.log_error("Get Webhook Config Error", str(e))
        return f'<div class="empty-state"><h3>Error loading webhook config</h3><p>{str(e)}</p></div>'

@frappe.whitelist()
def update_webhook_config():
    """Update webhook configuration for the current merchant"""
    try:
        user_id = frappe.session.user
        data = frappe.form_dict
        webhook_url = data.get("webhook_url", "")
        
        # Update webhook URL
        frappe.db.set_value("Merchant", user_id, "webhook_url", webhook_url)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Webhook URL updated successfully"
        }
    except Exception as e:
        frappe.log_error("Update Webhook Config Error", str(e))
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_whitelist_ips():
    """Get whitelisted IPs for the current merchant"""
    try:
        user_id = frappe.session.user
        
        ips = frappe.db.sql("""
            SELECT name, whitelisted_ip, creation
            FROM `tabWhitelist IP`
            WHERE merchant = %s
            ORDER BY creation DESC
        """, (user_id,), as_dict=True)
        
        context = {
            "ips": ips
        }
        
        html = frappe.render_template("templates/includes/whitelist_ips.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get Whitelist IPs Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error loading whitelisted IPs</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def add_whitelist_ip():
    """Add a new whitelisted IP for the current merchant"""
    try:
        user_id = frappe.session.user
        data = frappe.form_dict
        ip_address = data.get("ip_address", "")
        
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
            "message": "IP address whitelisted successfully"
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
        user_id = frappe.session.user
        data = frappe.form_dict
        ip_name = data.get("ip_name", "")
        
        # Verify the IP belongs to the current merchant
        merchant = frappe.db.get_value("Whitelist IP", ip_name, "merchant")
        
        if merchant != user_id:
            return {
                "success": False,
                "error": "Unauthorized"
            }
        
        frappe.delete_doc("Whitelist IP", ip_name, ignore_permissions=True)
        frappe.db.commit()
        
        # Return updated list
        return get_whitelist_ips()
        
    except Exception as e:
        frappe.log_error("Delete Whitelist IP Error", str(e))
        return Response(f'<div class="empty-state"><h3>Error deleting IP</h3><p>{str(e)}</p></div>')

@frappe.whitelist()
def get_merchant_profile():
    """Get merchant profile information for sidebar"""
    try:
        user_id = frappe.session.user
        
        # Get merchant info
        merchant = frappe.db.get_value("Merchant", user_id, 
            ["company_name", "status", "company_email", "contact_detail"], as_dict=True)
        
        context = {
            "merchant": {
                "company_name": merchant.get("company_name", "Merchant") if merchant else "Merchant",
                "status": merchant.get("status", "Pending") if merchant else "Pending",
                "email": merchant.get("company_email", "") if merchant else "",
                "phone": merchant.get("contact_detail", "") if merchant else ""
            }
        }
        
        html = frappe.render_template("templates/includes/merchant_profile.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get Merchant Profile Error", str(e))
        return Response('<div style="padding: 1rem; color: rgba(255,255,255,0.7); font-size: 0.75rem;">Error loading profile</div>')

@frappe.whitelist()
def get_merchant_profile_page():
    """Get full merchant profile data for the profile page"""
    try:
        user_id = frappe.session.user
        
        # Get all merchant fields
        merchant = frappe.get_doc("Merchant", user_id)
        
        # Get virtual accounts for this merchant
        virtual_accounts = frappe.db.sql("""
            SELECT 
                name,
                account_number,
                ifsc,
                status,
                creation
            FROM `tabVirtual Account`
            WHERE merchant = %s
            ORDER BY creation DESC
        """, (user_id,), as_dict=True)
        
        context = {
            "merchant": {
                "company_name": merchant.company_name or "",
                "company_email": merchant.company_email or "",
                "contact_detail": merchant.contact_detail or "",
                "status": merchant.status or "Pending",
                "pan": merchant.pancard or "",
                "gstin": merchant.gstin or "",
                "creation": merchant.creation.strftime("%d %b %Y") if merchant.creation else ""
            },
            "virtual_accounts": virtual_accounts
        }
        
        html = frappe.render_template("templates/includes/merchant_profile_page.html", context)
        return html
        
    except Exception as e:
        frappe.log_error("Get Merchant Profile Page Error", str(e))
        return '<div style="padding: 2rem; text-align: center;"><p style="color: #ef4444;">Error loading profile data</p></div>'


@frappe.whitelist()
def get_ip_whitelist():
    """Get whitelisted IPs for the merchant"""
    try:
        user_id = frappe.session.user
        
        # Get whitelisted IPs for this merchant
        whitelisted_ips = frappe.db.sql("""
            SELECT 
                name,
                whitelisted_ip,
                creation,
                modified
            FROM `tabWhitelist IP`
            WHERE merchant = %s
            ORDER BY creation DESC
        """, (user_id,), as_dict=True)
        
        context = {
            "whitelisted_ips": whitelisted_ips
        }
        
        html = frappe.render_template("templates/includes/ip_whitelist.html", context)
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get IP Whitelist Error", str(e))
        return Response('<div style="padding: 2rem; text-align: center;"><p style="color: #ef4444;">Error loading IP whitelist</p></div>')


@frappe.whitelist()
def add_whitelisted_ip(whitelisted_ip):
    """Add a new whitelisted IP for the merchant"""
    try:
        user_id = frappe.session.user
        
        # Check if IP already exists for this merchant
        exists = frappe.db.exists("Whitelist IP", {
            "merchant": user_id,
            "whitelisted_ip": whitelisted_ip
        })
        
        if exists:
            return {"success": False, "error": "This IP address is already whitelisted"}
        
        # Create new whitelisted IP
        ip_doc = frappe.get_doc({
            "doctype": "Whitelist IP",
            "merchant": user_id,
            "whitelisted_ip": whitelisted_ip
        })
        ip_doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": "IP address added successfully"}
        
    except Exception as e:
        frappe.log_error("Add Whitelisted IP Error", str(e))
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def delete_whitelisted_ip(ip_name):
    """Delete a whitelisted IP"""
    try:
        user_id = frappe.session.user
        
        # Verify the IP belongs to this merchant
        ip_doc = frappe.get_doc("Whitelist IP", ip_name)
        
        if ip_doc.merchant != user_id:
            return {"success": False, "error": "Unauthorized"}
        
        frappe.delete_doc("Whitelist IP", ip_name, ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": "IP address deleted successfully"}
        
    except Exception as e:
        frappe.log_error("Delete Whitelisted IP Error", str(e))
        return {"success": False, "error": str(e)}



@frappe.whitelist()
def get_wallet_balance_header():
    """Get wallet balance and merchant name for the header display"""
    try:
        user_id = frappe.session.user
        
        # Get wallet balance
        wallet = frappe.db.get_value("Wallet", user_id, ["balance", "status"], as_dict=True)
        
        # Get merchant info
        merchant = frappe.db.get_value("Merchant", user_id, ["company_name"], as_dict=True)
        
        balance = float(wallet.get("balance", 0)) if wallet else 0
        merchant_name = merchant.get("company_name", "Merchant") if merchant else "Merchant"
        
        html = f'''
        <div class="page-header" style="display: flex; justify-content: space-between; align-items: center; gap: 1.25rem; margin-bottom: 1.5rem;">
            <div style="flex: 1;">
                <h1 style="margin: 0 0 0.5rem 0; font-size: 2rem; font-weight: 700; color: #4A3F8F;">Welcome back, {merchant_name}</h1>
                <p style="margin: 0; color: #5A4E8F; font-size: 1rem;">Here's what's happening with your account today</p>
            </div>
            <div id="wallet-balance-header"
                style="flex-shrink: 0; display: flex; align-items: center; gap: 1rem; padding: 1rem 1.25rem; background: linear-gradient(135deg, #4A3F8F 0%, #6B5FB8 100%); border-radius: 12px; color: white; box-shadow: 0 4px 12px rgba(74, 63, 143, 0.25);">
                <div>
                    <div
                        style="font-size: 0.6875rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 0.25rem;">
                        Wallet Balance</div>
                    <div id="wallet-balance-amount"
                        style="font-size: 1.5rem; font-weight: 700; letter-spacing: -0.5px;">₹{balance:,.2f}</div>
                </div>
                <div style="padding: 0.625rem; background: rgba(255,255,255,0.15); border-radius: 10px;">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                </div>
            </div>
        </div>
        '''
        return Response(html)
        
    except Exception as e:
        frappe.log_error("Get Wallet Balance Header Error", str(e))
        return Response(f'<div class="page-header" style="display: flex; justify-content: space-between; align-items: center; gap: 2rem; margin-bottom: 2rem;"><div style="flex: 1;"><h1 style="margin: 0 0 0.25rem 0; font-size: 1.875rem;">Welcome back</h1><p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Error loading header</p></div><div id="wallet-balance-header" style="flex-shrink: 0; padding: 0.875rem 1.5rem; color: #ef4444;">Error loading balance</div></div>')

import frappe
import json
import hmac
import hashlib
import base64
from typing import Dict, Any, Tuple
from frappe import _
from frappe.utils import now, get_datetime

@frappe.whitelist(allow_guest=True)
def blinkpe_webhook():
    """
    Blinkpe webhook endpoint to handle payment notifications.
    """
    try:
        if frappe.request.method != "POST":
            return frappe.response.update({
                "http_status_code": 405,
                "message": "Only POST method allowed",
                "status": "failed"
            })

        # Parse JSON payload
        try:
            payload = json.loads(frappe.request.data)
            webhook = frappe.get_doc({
                "doctype":"Blinkpe Webhook",
                "webhook_data":payload,
                "integration": "Airtel Payment Bank"
            }).insert(ignore_permissions=True)
            webhook.submit()
            frappe.db.commit()

            return {"status": "success", "message": "Webhook processed"}
            
        except json.JSONDecodeError:
            frappe.log_error("Invalid JSON in webhook request", "Xettle Webhook")
            return frappe.response.update({
                "http_status_code": 400,
                "message": "Invalid JSON payload",
                "status": "failed"
            })

    except Exception as e:
        frappe.log_error("Webhook processing error", str(e))
        return {
            "http_status_code": 500,
            "message": "Internal server error",
            "status": "failed"
        }


def process_webhook(doc, method):
    frappe.db.savepoint("webhook_process")
    try:
        webhook_response, integration = frappe.db.get_value(
            "Blinkpe Webhook", doc.name, ["webhook_data", "integration"]
        )

        payload = json.loads(webhook_response)

        if integration == "Airtel Payment Bank":
            process_airtel_webhook(payload)

    except Exception as e:
        frappe.log_error("Error in processing webhook", str(e))
        frappe.db.rollback(save_point = "webhook_process")


def process_airtel_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    
    try:
        utr = payload.get("rrn")
        order_id = payload.get("hdnOrderID")
        status = payload.get("txnStatus")
        remark = payload.get("messageText")
        doc = frappe.get_doc("Order",order_id)

        frappe.set_user(doc.merchant_ref_id)

        transaction = frappe.get_doc("Transaction",{"order":order_id})
        
        # Process based on status
        if status == "SUCCESS":
            transaction.status = "Success"
            transaction.transaction_reference_id = utr
            transaction.remark = remark
            transaction.save(ignore_permissions=True)
            transaction.submit()
            
            doc.status = "Processed"
            doc.utr = utr
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            
        elif status == "FAILURE":
            txn_status = "Failed"

            transaction.status = txn_status
            transaction.remark = remark
            transaction.save(ignore_permissions=True)
            transaction.submit()

            handle_transaction_failure(client_order_id,txn_status,txn_status,transaction.name)
        
    except Exception as e:
        frappe.log_error(f"Error processing webhook: {str(e)}", "Swavenpay Webhook Processing")
        return {"success": False, "error": str(e)}
        
def handle_transaction_failure(name, status, error_message, transaction_id):
    """
    Common function to handle transaction failures and refund wallet
    """
    try:

        doc = frappe.get_doc("Order", name)

        frappe.set_user(doc.merchant_ref_id)

        # wallet_row = frappe.db.sql("""
        #     SELECT balance FROM `tabWallet`
        #     WHERE name = %s FOR UPDATE
        # """, (doc.merchant_ref_id,), as_dict=True)
        balance = frappe.db.get_value("Wallet", doc.merchant_ref_id, "balance") or 0.0

        frappe.db.sql("""
            UPDATE `tabWallet`
            SET balance = balance + %s
            WHERE name = %s
        """, (doc.transaction_amount, doc.merchant_ref_id))
        
        new_balance = float(balance) + float(doc.transaction_amount)
        
        ledger = frappe.get_doc({
            "doctype": 'Ledger',
            "order": doc.name,
            "transaction_type": 'Credit',
            'status': 'Reversed',
            'transaction_id': transaction_id,
            'client_ref_id': doc.client_ref_id,
            'opening_balance': balance,
            "closing_balance": new_balance
        }).insert(ignore_permissions=True)
        ledger.submit()
                
        # Refund Xettle Wallet
        wallet = frappe.get_single("Xettle Wallet")
        frappe.db.set_value("Xettle Wallet", None, "tax", float(wallet.tax) - float(doc.tax))
        frappe.db.set_value("Xettle Wallet", None, "fee", float(wallet.fee) - float(doc.fee))
        
        doc.status = 'Reversed'
        doc.cancellation_reason = error_message[:100]
        doc.cancelled_at = frappe.utils.now()
        doc.save(ignore_permissions=True)

        #frappe.db.commit()

    except Exception as refund_error: 
        frappe.db.rollback(save_point = "webhook_process")
        frappe.log_error("Error",refund_error)

@frappe.whitelist()
def update_webhook(webhook_url):
    try:
        user = frappe.session.user
        merchant = frappe.get_doc("Merchant", user)

        exists = frappe.db.exists("Webhook", user, cache=True)
        if not exists:
            frappe.get_doc({
                'doctype': 'Webhook',
                '__newname': user,
                'webhook_doctype': 'Transaction',
                'webhook_docevent': 'on_submit',
                'condition': f"(doc.merchant == '{user}') and (doc.status in ['Success', 'Failed', 'Reversed'])",
                'request_url': webhook_url,
                'request_method': 'POST',
                'request_structure': 'JSON',
                'background_jobs_queue': 'long',
                'webhook_json': 
                """{
                    "crn":"{{doc.order}}",
                    "utr":"{{doc.transaction_reference_id}}",
                    "status": "{{doc.status}}",
                    "clientRefID": "{{doc.client_ref_id}}"
                }"""
            }).insert(ignore_permissions=True)

            merchant.webhook = webhook_url
            merchant.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "created"}

        elif merchant.webhook != webhook_url:
            webhook_doc = frappe.get_doc("Webhook", user)
            webhook_doc.request_url = webhook_url
            webhook_doc.save(ignore_permissions=True)

            merchant.webhook = webhook_url
            merchant.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "updated"}
        
        else:
            # Webhook URL is the same, no update needed
            return {"status": "unchanged"}

    except Exception as e:
        frappe.log_error("Error in webhook updation", str(e))
        return {"status": "error", "message": str(e)}



@frappe.whitelist(allow_guest=True)
def airtelbank():
    """
    Handle Airtel Bank webhook callbacks
    """
    try:
        # Get the webhook data from request
        if frappe.request.method != "POST":
            frappe.throw(_("Only POST requests are allowed"))
        
        # Parse JSON data from webhook
        webhook_data = frappe.request.get_json()
        
        # Log the webhook for debugging
        frappe.log_error(
            message=frappe.as_json(webhook_data),
            title="Airtel Bank Webhook Received"
        )
        
        # Process your webhook data here
        # Example: Create a document, update status, etc.
        process_webhook(webhook_data)
        
        # Return success response
        return {
            "status": "success",
            "message": "Webhook received successfully"
        }
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="Airtel Bank Webhook Error"
        )
        return {
            "status": "error",
            "message": str(e)
        }

def process_webhook(data):
    """
    Process the webhook data
    """
    # Your business logic here
    # Example: Update payment status, create documents, etc.
    pass
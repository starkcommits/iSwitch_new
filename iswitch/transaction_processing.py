import frappe
import requests
import jwt
import json
from datetime import datetime as dt, timedelta as td
import hashlib
from .bank import JSONEncryptionDecryption
from frappe.utils import today, getdate


def handle_transaction_failure(name, status, error_message, transaction_id):
    """
    Common function to handle transaction failures and refund wallet
    """
    try:
        doc = frappe.get_doc("Order", name)

        # wallet_row = frappe.db.sql("""
        #     SELECT balance FROM `tabWallet`
        #     WHERE name = %s FOR UPDATE
        # """, (doc.merchant_ref_id,), as_dict=True)
        frappe.set_user(doc.merchant_ref_id)

        balance = frappe.db.get_value("Wallet", doc.merchant_ref_id, "balance") or 0.0
        
        # balance = float(wallet_row[0]["balance"]) or 0.0
        # Apply balance change safely
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
            'closing_balance': new_balance
        }).insert(ignore_permissions=True)
        ledger.submit()
                
        # Refund Xettle Wallet
        wallet = frappe.get_single("Xettle Wallet")
        frappe.db.set_value("Xettle Wallet", None, "tax", float(wallet.tax) - float(doc.tax))
        frappe.db.set_value("Xettle Wallet", None, "fee", float(wallet.fee) - float(doc.fee))
        
        doc.status = status
        doc.cancellation_reason = error_message[:100]
        doc.cancelled_at = frappe.utils.now()
        doc.save(ignore_permissions=True)

    except Exception as refund_error: 
        frappe.db.rollback(save_point = "process_transaction")
        frappe.log_error("Error in handling failed transaction",refund_error)

def handle_transaction(doc,method):
    if doc.transaction_type == "Debit":
        try:
            transaction = frappe.get_doc("Transaction",doc.transaction_id)
            order = frappe.get_doc("Order",transaction.order)
            if order.product =="UPI":
                upi_transaction_processing(order,transaction)
                
        except Exception as e:
            transaction = frappe.get_doc("Transaction", doc.transaction_id)
            transaction.status = "Failed"
            transaction.save(ignore_permissions=True)
            transaction.submit()

            handle_transaction_failure(doc.order,"Cancelled","Failed",transaction.name)
            frappe.log_error("Error in transaction handling",str(e))

def upi_transaction_processing(doc,transaction):
    try:
        doc.status = "Processing"
        doc.save(ignore_permissions=True)
        
        frappe.db.savepoint("process_transaction")

        processor = frappe.get_doc("Integration", doc.integration_id)
        
        frappe.set_user(doc.merchant_ref_id)

        status = "Pending"
        remark = ""
        utr = ""
        crn = ""

        if processor.name == "Airtel Payment Bank":
            headers = {
                "Content-Type": "application/v2+json "
            }
            
            payload = {
                "amount": str(doc.order_amount),
                "feSessionId": doc.name,
                "hdnOrderID": doc.name,
                "mid": processor.get_password("client_id"),
                "payeeVirtualAdd": "AnshikaFintech@appl",
                "payerMobNo": "9999999999",
                "payerVirtualAdd": doc.vpa,
                "remarks": "Payout",
                "ver": "2.0"
            }

            hash_string = get_hash_string(payload, processor.get_password("secret_key"))
            hash_code = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

            payload["hash"] = hash_code

            url = processor.api_endpoint.rstrip("/") + "/upiMerCollect"
            api_response = requests.post(url, headers = headers, json = payload, timeout = 30)

            try:
                api_data = api_response.json()
                frappe.log_error("API Response", api_data)
                crn = api_data.get("rrn")
                remark = api_data.get("messageText")

            except Exception as e:
                frappe.log_error("API Response", api_response.text)
            
        if status == "Failed" or status == "Reversed":
            txn = frappe.db.get_value("Transaction",{"order":doc.name, "merchant":doc.merchant_ref_id}, ['name'])
            transaction = frappe.get_doc("Transaction", txn)
            transaction.status = status
            transaction.remark = remark
            transaction.crn = crn
            transaction.save(ignore_permissions=True)
            transaction.submit()
            
            if status == "Failed":
                status = "Cancelled"

            handle_transaction_failure(doc.name,status,remark,transaction.name)

        elif status == "Success":
            txn = frappe.db.get_value("Transaction",{"order":doc.name, "merchant":doc.merchant_ref_id}, ['name'])
            transaction = frappe.get_doc("Transaction", txn)
            
            transaction.status = status
            transaction.crn = crn
            transaction.transaction_reference_id = utr
            transaction.save(ignore_permissions=True)
            transaction.submit()

            doc.status = "Processed"
            doc.utr = utr
            doc.save(ignore_permissions=True)
        
        elif status == "Pending":
            txn = frappe.db.get_value("Transaction",{"order":doc.name, "merchant":doc.merchant_ref_id}, ['name'])
            transaction = frappe.get_doc("Transaction", txn)
            
            transaction.status = status
            transaction.crn = crn
            transaction.remark = remark
            transaction.save(ignore_permissions=True)
            
    except Exception as e:
        frappe.db.rollback(save_point = "process_transaction")
        frappe.log_error("Error in transaction processing",str(e))


def get_hash_string(payload, secret_key):
    """
    Dynamically generate hash string from all payload fields.
    """
    try:
        # Get all payload values in the order they were defined
        hash_parts = [str(value) for value in payload.values()]
        
        # Add secret key at the end
        hash_parts.append(secret_key)
        
        # Join with # delimiter
        hash_string = "#".join(hash_parts)
        
        return hash_string
        
    except Exception as e:
        frappe.log_error("Error in hash string generation", str(e))
        raise


import frappe
import requests
import jwt
import json
from datetime import datetime as dt, timedelta as td
import hashlib
from .bank import JSONEncryptionDecryption

def generate_hash(merchant_id, parameters, hashing_method, secret_key, key_order):
    hash_data = str(merchant_id)
    
    for key in key_order:
        value = parameters[key]
        # Convert to string in JavaScript-like manner
        if isinstance(value, float) and value.is_integer():
            # Convert float like 10.0 to "10" (like JavaScript)
            value_str = str(int(value))
        else:
            value_str = str(value)
        hash_data += '|' + value_str
    
    hash_data += '|' + str(secret_key)
    
    if len(hash_data) > 0:
        # Create hash using the specified method
        hash_obj = hashlib.new(hashing_method)
        hash_obj.update(hash_data.encode('utf-8'))
        return hash_obj.hexdigest().lower()
    
    return None

def generate_token(processor):
    try:
        expiration_time = dt.utcnow() + td(days=1)
        secret_key = processor.get_password("secret_key")

        token = jwt.encode(
            {
                "merchant_id": "BM594874",
                "name": "Satinfra Recharge",
                "email": "satsoftwareprivatelimited@gmail.com",
                "exp": expiration_time,
            },
            secret_key,
            algorithm="HS256",
        )

        return token
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Token Generation Failed")
        return None


@frappe.whitelist(allow_guest=True)
def update_record():
    results = frappe.db.sql("""
        SELECT name, integration_id FROM `tabOrder`
        WHERE status IN ('Queued', 'Processing')
    """, as_dict=True)
    frappe.log_error("Order to processed",results)
    
    for result in results:
        frappe.db.savepoint("status_process")
        try:
            txn_status = ""
            utr = ""

            if result.integration_id == "Airtel Payment Bank":

                processor = frappe.get_doc("Integration", result.integration_id)
                rrn = frappe.db.get_value("Transaction",{"order":result.name},'crn')
                headers = {
                    "Content-Type": "application/v2+json"
                }

                payload = {
                    "channel": processor.get_password("client_id"),
                    "feSessionId": result.name,
                    "hdnOrderID": result.name,
                    "merchantId": processor.get_password("client_id"),
                    "ver": "2.0",
                    "rrn": rrn
                }
                hash_string = get_hash_string(payload,processor.get_password("secret_key"))

                hash_code = hashlib.sha512(hash_string.encode('utf-8')).hexdigest()

                payload["hash"] = hash_code

                url = processor.api_endpoint.rstrip("/") + "/upiMerCollectCheckTxn"
                api_response = requests.post(url, headers = headers, json = payload, timeout = 30)

                try:
                    api_data = api_response.json()
                    frappe.log_error(f"Requery API Response {result.name}", api_data)
                    status = api_data.get("txnStatus")
                    if status == "SUCCESS":
                        txn_status = "Success"
                    elif status == "FAILURE":
                        txn_status = "Failed"
                    
                except Exception as e:
                    frappe.db.rollback(save_point = "status_process")
                    frappe.log_error(f"Error in requery {result.name}", api_response.text)
            
            if txn_status == "Success":
                doc = frappe.get_doc("Order", result.name)
                frappe.set_user(doc.merchant_ref_id)
                
                name = frappe.db.get_value("Transaction",{"order":doc.name}, ['name'])
                
                transaction = frappe.get_doc("Transaction",name)
                if transaction.docstatus != 1:
                    transaction.status = txn_status
                    transaction.transaction_reference_id = utr
                    transaction.remark = "Transaction Completed"
                    transaction.save(ignore_permissions=True)
                    transaction.submit()

                    doc.status = "Processed"
                    doc.utr = utr
                    doc.save(ignore_permissions=True)
                    frappe.db.commit()

            elif txn_status == "Failed" or txn_status == "Reversed":
                
                doc = frappe.get_doc("Order", result.name)
                frappe.set_user(doc.merchant_ref_id)

                name = frappe.db.get_value("Transaction",{"order":doc.name, "merchant":doc.merchant_ref_id}, ['name'])
                transaction = frappe.get_doc("Transaction",name)
                
                if transaction.docstatus == 0:
                    transaction.status = txn_status
                    transaction.remark = "Failed transaction"
                    transaction.save(ignore_permissions=True)
                    transaction.submit()
        
                    if txn_status == "Failed":
                        txn_status = "Cancelled"

                    handle_transaction_failure(doc.name, txn_status, txn_status, transaction.name)

                    frappe.db.commit()
        except Exception as e:
            frappe.db.rollback(save_point = "status_process")
            frappe.log_error(frappe.get_traceback(), f"Error updating transaction for Order: {result.name}")



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

        # balance = float(wallet_row[0]["balance"])
        balance = frappe.db.get_value("Wallet", doc.merchant_ref_id, "balance") or 0.0
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
                
        
        doc.status = 'Reversed'
        doc.cancellation_reason = error_message[:100]
        doc.cancelled_at = frappe.utils.now()
        doc.save(ignore_permissions=True)

        #frappe.db.commit()

    except Exception as e:
        frappe.db.rollback(save_point = "status_process")
        frappe.log_error("error in handling transaction",str(e))


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

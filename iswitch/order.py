import frappe
from frappe import _
import requests
import json
import jwt
from datetime import datetime as dt, timedelta as td

def generate_token(processor):
    try:
        expiration_time = dt.utcnow() + td(days=7)
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

def handle_transaction_failure(name, status, error_message, transaction_id):
    """
    Common function to handle transaction failures and refund wallet
    """
    try:

        doc = frappe.get_doc("Order", name)

        wallet_row = frappe.db.sql("""
            SELECT balance FROM `tabWallet`
            WHERE name = %s FOR UPDATE
        """, (doc.merchant_ref_id,), as_dict=True)

        frappe.set_user(doc.merchant_ref_id)
        balance = float(wallet_row[0]["balance"]) or 0.0
        # Apply balance change safely
        new_balance = float(wallet_row[0]["balance"]) + float(doc.transaction_amount)

        frappe.db.sql("""
            UPDATE `tabWallet`
            SET balance = %s
            WHERE name = %s
        """, (new_balance, doc.merchant_ref_id))

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
        
        doc.status = status
        doc.cancellation_reason = error_message[:100]
        doc.cancelled_at = frappe.utils.now()
        doc.save(ignore_permissions=True)

        frappe.db.commit()

    except Exception as refund_error: 
        frappe.db.rollback(save_point = "update_record")
        frappe.log_error("Error",refund_error)


@frappe.whitelist()
def create_order():
    data = frappe.request.get_json()

    ip_address = None
    user_id = None
    if frappe.request.headers.get('X-Real-Ip'):
        ip_address = frappe.request.headers.get('X-Real-Ip').split(',')[0]
    else:
        ip_address = frappe.request.remote_addr
    
    auth_header = frappe.get_request_header("Authorization")

    request_response = frappe.get_doc({
        "doctype":"Request Response",
        "request": data,
        "header": auth_header,
        "user": user_id
    }).insert(ignore_permissions=True)

    if not auth_header or not auth_header.lower().startswith("token "):
        response = {
            "code": "0x0401",
            "status": "MISSING_HEADER",
            "message": "Authorization header is missing."
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response
    try:
        # Split token and extract parts
        token = auth_header[6:].strip()  # Remove "token " prefix
        api_key, api_secret = token.split(":")
    except ValueError as e:
        frappe.log_error("Error in header extraction",str(e))
        response = {
            "Error in token format. Please verify and try again."
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()

        return response
        
    user_id = frappe.db.get_value("User", {"api_key": api_key},'email')

    frappe.set_user(user_id)

    if not frappe.db.exists("Whitelist IP",{'merchant':user_id,'whitelisted_ip':ip_address}):
        response = {
            "code": "0x0401",
            "status": "UNAUTHORIZED ACCESS", 
            "message": f"Originating IP {ip_address} is blocked by central firewall system. This incident will be reported."
        }

        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()

        return response

    if user_id == "Guest":
        response = {
            "code": "0x0401",
            "status": "UNAUTHORIZED", 
            "message": "Authentication required"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    merchant = frappe.get_doc("Merchant", user_id)
    if merchant.status != "Approved":
        response =  {
            "code": "0x0404",
            "status": "VALIDATION_ERROR",
            "message": "Validation failed",
            "data": f"Your Account is in {merchant.status} stage. Please contact Admin"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response 

    if not merchant.integration:
        response =  {
            "code": "0x0404",
            "status": "VALIDATION_ERROR",
            "message": "Validation failed",
            "data": "Processor isn't configured yet to process your order. Please try after sometime."
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    wallet = frappe.get_doc("Wallet", merchant.name)
    if wallet.status != "Active":
        response = {
                "code": "0x0404",
                "status": "VALIDATION_ERROR",
                "message": "Validation failed",
                "data": f"Your Wallet is {wallet.status}. Please contact Admin"
            }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response
    
    if "mode" not in data:
        response = {
            "code": "0x0203",
            "status": "MISSING_PARAMETER",
            "message": "mode is required"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    product = frappe.db.exists("Product", {"product_name": data["mode"].upper(), "is_active":1})
    if not product:
        response = {
            "code": "0x0500",
            "status": "SERVER_DOWN",
            "message":{ 
                f"{data['mode']}":[
                    f"{data['mode']} payment mode is down. Please try again after sometime."
                ] 
            }
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    order_amount = float(data["amount"])

    product_pricing = frappe.db.sql("""
        SELECT tax_fee_type, tax_fee, fee_type, fee
        FROM `tabProduct Pricing`
        WHERE parent = %s AND product = %s
        AND %s >= start_value AND %s <= end_value
    """, (merchant.name, data["mode"].upper(), order_amount, order_amount), as_dict=True)
    
    if not product_pricing:
        response = {
            "code": "0x0404",
            "status": "VALIDATION_ERROR",
            "message": "Validation failed",
            "data": "This payment mode or transaction limit is not active for you. Please contact Admin"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    processor = frappe.get_doc("Integration", merchant.integration)

    mode_verification = frappe.db.sql("""
        SELECT tax_fee_type, tax_fee, fee_type, fee
        FROM `tabProduct Pricing`
        WHERE parent = %s AND product = %s
    """, (processor.name, data["mode"].upper()), as_dict=True)

    if not mode_verification:
        response = {
            "code": "0x0404",
            "status": "VALIDATION_ERROR",
            "message": "Validation failed",
            "data": "This payment mode is not active for now. Please contact Admin"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    # frappe.log_error("User",user_id)
    fields = ["customer_name", "accountNo", "ifsc", "bank", "amount", "purpose", "mode", "clientRefId"]
    if data.get("mode","").upper() == "UPI":
        fields = ["customer_name", "customer_email", "customer_phone", "amount", "purpose", "clientRefId"]

    frappe.db.savepoint("start_transaction") 
    try:
        
        # Field validation
        for field in fields:
            if field not in data or not data[field]:
                frappe.db.rollback(save_point = "start_transaction")
                response = {
                    "code": "0x0203",
                    "status": "MISSING_PARAMETER", 
                    "message": {f"{field}": [f"{field} is missing."]}
                }
                # request_response = frappe.get_doc("Request Response", request_response.name)
                request_response.response = json.dumps(response)
                request_response.submit()
                return response

        # Check duplicate client ref id
        existing_order = frappe.db.exists("Order", {"client_ref_id": data["clientRefId"]})
        if existing_order:
            frappe.db.rollback(save_point = "start_transaction")
            response = {
                "code": "0x0203",
                "status": "MISSING_PARAMETER",
                "message": {"clientRefId": ["Client Ref Id already exists."]}
            }
            # request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        # Calculate fees and total amount
        processor = frappe.get_doc("Integration", merchant.integration)
        pricing = product_pricing[0]
        fee = float(pricing.get("fee", 0))
        tax = 0

        if pricing["fee_type"] == "Percentage":
            fee = (order_amount * float(pricing.get("fee", 0))) / 100

        if pricing["tax_fee_type"] == "Percentage":
            tax = (fee * float(pricing.get("tax_fee", 0))) / 100

        total_amount = order_amount + fee + tax

        wallet_row = frappe.db.sql("""
            SELECT balance FROM `tabWallet`
            WHERE name = %s FOR UPDATE
        """, (merchant.name,), as_dict=True)
        
        if not wallet_row:
            frappe.db.rollback(save_point = "start_transaction")
            response = {
                "code": "0x0404",
                "status": "VALIDATION_ERROR",
                "message": "Validation failed",
                "data": "No active wallet found"
            }
            request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response
            
        balance = float(wallet_row[0].balance) or 0.0

        if balance < total_amount:
            frappe.db.rollback(save_point = "start_transaction")
            response = {
                "code": "0x0404",
                "status": "VALIDATION_ERROR",
                "message": "Validation failed",
                "data": "Insufficient wallet balance"
            }
            request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        new_balance = balance - total_amount

        frappe.db.sql("""
            UPDATE `tabWallet`
            SET balance = %s
            WHERE name = %s
        """, (new_balance, merchant.name))

        # UPDATE XETTLE WALLET (PLATFORM FEES)
        xettle_wallet = frappe.get_single("Xettle Wallet")
        frappe.db.set_value("Xettle Wallet", None, "tax", float(xettle_wallet.tax) + float(tax))
        frappe.db.set_value("Xettle Wallet", None, "fee", float(xettle_wallet.fee) + float(fee))

        # CREATE ORDER
        order = None
        if data.get("mode", "").upper() != "UPI":
            order = frappe.get_doc({
                "doctype": "Order",
                "customer_name": data["customer_name"],
                "customer_account_number": data["accountNo"],
                "ifsc": data["ifsc"],
                "bank": data["bank"].upper(),
                "order_amount": order_amount,
                "purpose": data["purpose"],
                "product": data["mode"].upper(),
                "merchant_ref_id": merchant.name,
                "narration": data.get("narration", ""),
                "remark": data.get("remark", ""),
                "client_ref_id": data["clientRefId"],
                "integration_id": processor.name,
                "tax": tax,
                "fee": fee,
                "transaction_amount": total_amount
            }).insert(ignore_permissions=True)
        else:

            order = frappe.get_doc({
                "doctype": "Order",
                "customer_name": data["customer_name"],
                "order_amount": order_amount,
                "purpose": data["purpose"],
                "product": "UPI",
                "merchant_ref_id": merchant.name,
                "integration_id": merchant.integration,
                "remark": data.get("remark", ""),
                "client_ref_id": data["clientRefId"],
                "integration_id": processor.name,
                "vpa": data.get("vpa",""),
                "tax": tax,
                "fee": fee,
                "transaction_amount": total_amount
            }).insert(ignore_permissions=True)

        # CREATE TRANSACTION
        transaction = frappe.get_doc({
            "doctype": 'Transaction',
            "order": order.name,
            "merchant": order.merchant_ref_id,
            "amount": order.order_amount,
            "integration": order.integration_id,
            "status": "Processing",
            "product": order.product,
            "transaction_date": frappe.utils.now()
        }).insert(ignore_permissions=True)

        # CREATE LEDGER ENTRY
        ledger = frappe.get_doc({
            "doctype": 'Ledger',
            "order": order.name,
            "transaction_type": 'Debit',
            'status': 'Success',
            'client_ref_id': order.client_ref_id,
            'transaction_id': transaction.name,
            'opening_balance': balance,
            'closing_balance': new_balance
        }).insert(ignore_permissions=True)
        ledger.submit()

        # FOR NON-UPI: Commit and return success
        if data.get("mode", "").upper() != "UPI":
            frappe.db.commit()
            response = {
                "code": "0x0200",
                "message": "Order accepted successfully",
                "status": "SUCCESS",
                "data": {
                    "clientRefId": order.client_ref_id,
                    "orderRefId": order.name,
                    "status": order.status
                }
            }
            #request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        # FOR UPI: Make API call within same transaction
        else:
            token = generate_token(processor)
            headers = {
                "Api-Key": processor.get_password("client_id"),
                "Authorization": f"Bearer {token}"
            }

            payload = {
                "epin_denomination": order_amount,
                "external_order_id": order.name,
                "delivery_details": {
                    "recipient_name": data["customer_name"],
                    "recipient_email": data["customer_email"],
                    "recipient_phone_number": data["customer_phone"],
                    "recipient_player_id": customer_id
                }
            }
            url = processor.api_endpoint.rstrip("/") + "/transaction/top-up/"
            
            # Make API call
            try:
                api_response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if api_response.status_code != 200:
                    # API failed - rollback transaction
                    frappe.log_error("UPI API Failed", f"Status: {api_response.status_code}, Response: {api_response.text}")
                    frappe.db.rollback(save_point = "start_transaction")
                    
                    response = {
                        "code": "0x0500",
                        "status": "ERROR", 
                        "message": "UPI transaction failed"
                    }
                    #request_response = frappe.get_doc("Request Response", request_response.name)
                    request_response.response = json.dumps(response)
                    request_response.submit()
                    return response
                
                try:
                    response_data = api_response.json()
                    api_data = response_data.get("data", {})
                    
                    if not api_data:
                        # Empty response - rollback
                        frappe.db.rollback(save_point = "start_transaction")
                        response = {
                            "code": "0x0500",
                            "status": "ERROR",
                            "message": "Error in transaction processing"
                        }
                        #request_response = frappe.get_doc("Request Response", request_response.name)
                        request_response.response = json.dumps(response)
                        request_response.submit()
                        
                        return response
                    
                    # API successful - update order with payment URLs
                    order.payment_url = api_data.get("payment_url", "")
                    order.success_url = api_data.get("success_url", "")
                    order.failed_url = api_data.get("failed_url", "")
                    order.close_url = api_data.get("close_url", "")
                    order.save(ignore_permissions=True)
                    
                    # Commit transaction
                    frappe.db.commit()
                    
                    response = {
                        "message": "Order initialized successfully",
                        "payment_url": order.payment_url,
                        "success_url": order.success_url,
                        "failed_url": order.failed_url,
                        "close_url": order.close_url
                    }
                    #request_response = frappe.get_doc("Request Response", request_response.name)
                    request_response.response = json.dumps(response)
                    request_response.submit()
                    return response
                    
                except ValueError as json_error:
                    # Invalid JSON response - rollback
                    frappe.log_error("UPI API JSON Error", str(json_error))
                    frappe.db.rollback(save_point = "start_transaction")
                    
                    response = {
                        "code": "0x0500",
                        "status": "ERROR", 
                        "message": "UPI transaction failed"
                    }
                    #request_response = frappe.get_doc("Request Response", request_response.name)
                    request_response.response = json.dumps(response)
                    request_response.submit()
                    
                    return response
                    
            except requests.RequestException as req_error:
                # Network/timeout error - rollback
                frappe.log_error("UPI API Request Error", str(req_error))
                frappe.db.rollback(save_point = "start_transaction")
                response = {
                    "code": "0x0500",
                    "status": "ERROR",
                    "message": "UPI transaction failed"
                }
                #request_response = frappe.get_doc("Request Response", request_response.name)
                request_response.response = json.dumps(response)
                request_response.submit()
                
                return response

    except frappe.ValidationError as e:
        frappe.db.rollback(save_point = "start_transaction")
        response = {
            "code": "0x0400",
            "status": "VALIDATION_ERROR", 
            "message": "Validation failed",
            "data": str(e)
        }
        #request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        
        return response
        
    except Exception as e:
        frappe.db.rollback(save_point = "start_transaction")
        frappe.log_error("Order Creation Error", frappe.get_traceback())
        response = {
            "code": "0x0500",
            "status": "ERROR",
            "message": "Error in order creation",
            "data": str(e)
        }
        #request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

@frappe.whitelist()
def get_order_status():
    """Get order status using Token authentication"""
    data = frappe.request.get_json()
    auth_header = frappe.get_request_header("Authorization")
    if not auth_header or not auth_header.lower().startswith("token "):
        return {
            "Authorization header is missing."
        }
    
    try:
        # Split token and extract parts
        token = auth_header[6:].strip()  # Remove "token " prefix
        api_key, api_secret = token.split(":")
    except ValueError as e:
        frappe.log_error("Error in header extraction",str(e))
        return {
            "Error in token format. Please verify and try again."
        }

    user_id = frappe.db.get_value("User", {"api_key": api_key},'email')
    # frappe.log_error("User",user_id)
    request_response = frappe.get_doc({
        "doctype":"Request Response",
        "request": data,
        "header": auth_header,
        "user": user_id
    }).insert(ignore_permissions=True)
    
    if not data.get('orderRefId') and not data.get('clientRefId'):
        response = {
            "code": "0x0203",
            "status": "MISSING_PARAMETER",
            "message": "Either orderRefId or clientRefId is required"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()

        return response
    
    try:
        filters = {"merchant_ref_id": user_id}
        
        if data.get('orderRefId'):
            filters["name"] = data['orderRefId']
        elif data.get('clientRefId'):
            filters["client_ref_id"] = data['clientRefId']
        
        # order = frappe.get_doc("Order", filters)
        name = frappe.db.get_value("Order", filters)
        order = frappe.get_doc("Order", name)
        
        response = {
            "code": "0x0200",
            "status": "SUCCESS",
            "message": "Record fetched successfully.",
            "data": {
                "clientRefId": order.client_ref_id,
                "accountNo": order.customer_account_number,
                "orderRefId": order.name,
                "currency": "INR",
                "amount": order.order_amount,
                "fee": order.fee,
                "tax": order.tax,
                "mode": order.product,
                "utr": order.utr,
                "status": order.status
            }
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()

        return response
        
    except frappe.DoesNotExistError:
        response = {
            "code": "0x0404",
            "status": "NOT_FOUND",
            "message": "Order not found"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    except Exception as e:
        response = {
            "code": "0x0500",
            "status": "ERROR",
            "message": "Error fetching order status",
            "data": str(e)
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response
    pass

@frappe.whitelist()
def get_api_access():
    try:
        user_id = frappe.session.user
        user_doc = frappe.get_doc("User",user_id)

        user_doc.api_key = frappe.generate_hash(length=15)
        raw = frappe.generate_hash(length=30)
        user_doc.api_secret = raw
        user_doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {
            "public_key": user_doc.api_key,
            "secret_key": raw
        }
    except Exception as e:
        frappe.throw("Error in generating key",str(e))

@frappe.whitelist()
def get_wallet_balance():
    try:
        ip_address = ""
        if frappe.request.headers.get('X-Real-Ip'):
            ip_address = frappe.request.headers.get('X-Real-Ip').split(',')[0]
        else:
            ip_address = frappe.request.remote_addr
        
        auth_header = frappe.get_request_header("Authorization")
        if not auth_header or not auth_header.lower().startswith("token "):
            return {
                "Authorization header is missing."
            }
        
        try:
            # Split token and extract parts
            token = auth_header[6:].strip()  # Remove "token " prefix
            api_key, api_secret = token.split(":")
        except ValueError as e:
            frappe.log_error("Error in header extraction",str(e))
            return {
                "Error in token format. Please verify and try again."
            }

        user_id = frappe.db.get_value("User", {"api_key": api_key},'email')
        request_response = frappe.get_doc({
            "doctype":"Request Response",
            "header": auth_header,
            "user": user_id
        }).insert(ignore_permissions=True)

        if not frappe.db.exists("Whitelist IP",{'merchant':user_id,'whitelisted_ip':ip_address}):
            response = {
                "code": "0x0401",
                "status": "UNAUTHORIZED ACCESS", 
                "message": f"Originating IP {ip_address} is blocked by central firewall system. This incident will be reported."
            }
            request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        merchant = frappe.get_doc("Merchant", user_id)
        if merchant.status != "Approved":
            response = {
                "code": "0x0404",
                "status": "VALIDATION_ERROR",
                "message": "Validation failed",
                "data": f"Your Account is in {merchant.status} stage. Please contact Admin"
            }
            request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        balance, status = frappe.db.get_value("Wallet",user_id, ["balance","status"])

        response = {
            "message": "Wallet fetched successfully",
            "balance": balance,
            "status": status
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        return response

    except Exception as e:
        frappe.log_error("Error in fetching wallet balance", str(e))
        response = {
            "code": "0x0500",
            "status": "SERVER_ERROR",
            "message": "Error in fetching wallet"
        }
        request_response = frappe.get_doc("Request Response", request_response.name)
        request_response.response = json.dumps(response)
        request_response.submit()
        
        return response

@frappe.whitelist()
def get_existing_keys():
    try: 
        user_doc = frappe.get_doc("User", frappe.session.user)
        api_secret = user_doc.get_password("api_secret")
        api_key = user_doc.api_key

        return {
            "public_key": api_key,
            "secret_key": api_secret
        }
    except Exception as e:
        frappe.log_error("Error in key fetching",str(e))

@frappe.whitelist()
def get_merchant_details():
    try:
        result = frappe.db.sql("""
            SELECT 
                m.name, 
                m.company_name, 
                m.contact_detail, 
                m.status, 
                w.balance
            FROM tabMerchant m 
            JOIN tabWallet w ON m.name = w.name
        """, as_dict=True)
        return result
    except Exception as e:
        frappe.log_error("Error in record fetching")
        return {
            "Error in record fetching"
        }

@frappe.whitelist()
def get_card_data():
    try:
        result = frappe.db.sql("""
            SELECT 
                status,
                COUNT(name) AS payout_count,
                SUM(order_amount) AS payout_sum
            FROM tabOrder
            GROUP BY status
        """, as_dict=True)
        return result
    except Exception as e:
        frappe.log_error("Error in payout calcualtion",str(e))
        return {
            "Error in record fetching"
        }

@frappe.whitelist()
def get_merchant(merchant_name):
    try:
        # 1. Get Merchant Info
        merchant = frappe.db.sql("""
            SELECT 
                name, company_name, pancard, website, gstin,
                company_email, contact_detail, status, integration
            FROM `tabMerchant`
            WHERE name = %s
        """, merchant_name, as_dict=True)[0]

        # 2. Get Wallet Balance
        wallet = frappe.db.sql("""
            SELECT balance
            FROM `tabWallet`
            WHERE name = %s
        """, merchant_name, as_dict=True)

        # 3. Get Product Pricing
        product_pricing = frappe.db.sql("""
            SELECT product, start_value, end_value, fee_type, fee, tax_fee_type, tax_fee
            FROM `tabProduct Pricing`
            WHERE parent = %s
        """, merchant_name, as_dict=True)

        merchant["wallet_balance"] = wallet[0]["balance"] if wallet else 0
        merchant["product_pricing"] = product_pricing
        return merchant
    except Exception as e:
        frappe.log_error("Error in merchant record fetching",str(e))
        return {
            "Error in merchant record fetching"
        }

@frappe.whitelist()
def get_payout_report():
    try:
        result = frappe.db.sql("""
            SELECT
                SUM(CASE WHEN status = 'Processed' THEN order_amount ELSE 0 END) AS successful_payout,
                SUM(CASE WHEN status = 'Cancelled' THEN order_amount ELSE 0 END) AS failed_payout,
                SUM(CASE WHEN status = 'Processed' THEN tax ELSE 0 END) AS total_tax,
                SUM(CASE WHEN status = 'Processed' THEN fee ELSE 0 END) AS total_fee
            FROM tabOrder
        """, as_dict=True)[0]  # get first (and only) row as dict

        users = frappe.db.sql("""
            SELECT
                merchant_ref_id,
                SUM(CASE WHEN status = 'Processed' THEN order_amount ELSE 0 END) AS successful_payout,
                SUM(CASE WHEN status = 'Cancelled' THEN order_amount ELSE 0 END) AS failed_payout,
                SUM(CASE WHEN status = 'Processed' THEN tax ELSE 0 END) AS total_tax,
                SUM(CASE WHEN status = 'Processed' THEN fee ELSE 0 END) AS total_fee
            FROM tabOrder
            GROUP BY merchant_ref_id
        """, as_dict=True)

        result["users"] = users
        return result
    except Exception as e:
        frappe.log_error("Error in payout report fetching",str(e))
        return {
            "Error in payout report fetching"
        }

@frappe.whitelist()
def get_van_report():
    try:
        result = frappe.db.sql("""
            SELECT
                COUNT(name) AS total_van,
                SUM(amount) AS total_collection
            FROM `tabVirtual Account Logs`
        """, as_dict=True)[0]

        logs = frappe.db.sql("""
            SELECT
                account_number,
                SUM(amount) AS total_collection,
                merchant_email,
                merchant
            FROM `tabVirtual Account Logs`
            GROUP BY merchant_email
        """, as_dict=True)

        result["logs"] = logs

        return result
    except Exception as e:
        frappe.log_error("Error in van report fetching",str(e))
        return {
            "Error in van report fetching"
        }

@frappe.whitelist()
def update_transaction_status():
    frappe.db.savepoint("update_record")
    try:
        data = frappe.request.get_json()
        order_id = data.get("order_id","")
        status = data.get("status","")
        utr = data.get("utr","")
        remark = data.get("remark","")

        doc = frappe.get_doc("Order",order_id)

        frappe.set_user(doc.merchant_ref_id)

        transaction = frappe.get_doc("Transaction",{"order":order_id})

        if transaction.docstatus == 1:
            frappe.log_error(f"Transaction {transaction.name} is submitted. Current status: {transaction.docstatus}", "Webhook Processing")
            return {
                "Transaction is already submitted"
            }

        if status == "FAILED":
            transaction.status = "Failed"
            transaction.remark = remark
            transaction.save(ignore_permissions=True)
            transaction.submit()

            if status == "FAILED":
                status = "Cancelled"

            handle_transaction_failure(order_id,status,status,transaction.name)
            return {
                "Record updated successfully"
            }

        elif status == "REVERSED":
            transaction.status = "Reversed"
            transaction.remark = remark
            transaction.save(ignore_permissions=True)
            transaction.submit()

            status = "Reversed"

            handle_transaction_failure(order_id,status,status,transaction.name)
            return {
                "Record updated successfully"
            }
            
        elif status == "SUCCESS":
            transaction.status = "Success"
            transaction.transaction_reference_id = utr
            transaction.save(ignore_permissions=True)
            transaction.submit()
            
            doc.status = "Processed"
            doc.utr = utr
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {
                "Record updated successfully"
            }
        
    except Exception as e:
        frappe.db.rollback(save_point = "update_record")
        frappe.log_error("Error in transaction update",str(e))
        return {
            f"Error in transaction updation {str(e)}"
        }
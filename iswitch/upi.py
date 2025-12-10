import frappe
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
            secret_key,  # variable, not string
            algorithm="HS256",
        )

        return token
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Token Generation Failed")
        return None


@frappe.whitelist()
def initiate_upi():
    try:
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
            return {
                "Authorization header is missing."
            }
        
        try:
            # Split token and extract parts
            token = auth_header[6:].strip()  # Remove "token " prefix
            api_key, api_secret = token.split(":")
        except ValueError:
            frappe.log_error("Error in header extraction",str(e))
            return {
                "Error in token format. Please verify and try again."
            }

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
        
        product = frappe.db.exists("Product", {"product_name": data["mode"].upper(), "is_active":1})
        if not product:
            response = {
                "code": "0x0203",
                "status": "MISSING_PARAMETER",
                "message":{ 
                    f"{data['mode']}":[
                        f"{data['mode']} payment mode is not listed or enabled. Contact Admin for more details."
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
            AND %s >= start_value AND %s < end_value
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


        fields = ["customer_name", "customer_email", "customer_phone", "amount", "purpose", "clientRefId"]
        for field in fields:
            if field not in data or not data[field]:
                response = {
                    "code": "0x0203",
                    "status": "MISSING_PARAMETER",
                    "message": {
                        f"{field}": [
                            f"{field} is missing."
                        ]
                    }
                }
                request_response = frappe.get_doc("Request Response", request_response.name)
                request_response.response = json.dumps(response)
                request_response.submit()
                return response

        existing_order = frappe.db.exists("Order", {"client_ref_id": data["clientRefId"]})
        if existing_order:
            response = {
                "code": "0x0203",
                "status": "MISSING_PARAMETER",
                "message": {
                    "clientRefId": [
                        "Client Ref Id already exists."
                    ]
                }
            }
            request_response = frappe.get_doc("Request Response", request_response.name)
            request_response.response = json.dumps(response)
            request_response.submit()
            return response

        pricing = product_pricing[0]

        fee = float(pricing.get("fee",0))
        tax = 0

        # Handle platform fee calculation
        if pricing["fee_type"] == "Percentage":
            fee = (order_amount * float(pricing.get("fee",0))) / 100

         # Handle tax calculation
        if pricing["tax_fee_type"] == "Percentage":
            tax = (fee * float(pricing.get("tax_fee",0))) / 100

        # Now all values are floats, safe to add
        total_amount = order_amount + fee + tax
        
        wallet_row = frappe.db.sql("""
            SELECT balance FROM `tabWallet`
            WHERE name = %s FOR UPDATE
        """, (merchant.name,), as_dict=True)

        balance = float(wallet_row[0].balance) or 0.0

        if balance < total_amount:
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

        customer_id = None
        if not frappe.db.exists("Customer",{"mobile_number":data.get("customer_phone","")}):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": data.get("customer_name",""),
                "mobile_number": data.get("customer_phone",""),
                "email_id": data.get("customer_email")
            })
            customer_id = customer.name
        else:
            customer_id = frappe.db.get_value("Customer",{"mobile_number":data.get("customer_phone","")},'name')

        
        new_balance = balance - total_amount

        frappe.db.sql("""
            UPDATE `tabWallet`
            SET balance = %s
            WHERE name = %s
        """, (new_balance, merchant.name))

        wallet = frappe.get_single("Xettle Wallet")

        frappe.db.set_value("Xettle Wallet", None, "tax", float(wallet.tax) + float(tax))
        frappe.db.set_value("Xettle Wallet", None, "fee", float(wallet.fee) + float(fee))
        
        frappe.db.commit()

        order = frappe.get_doc({
            "doctype": "Order",
            "customer_id": customer_id,
            "customer_name": data["customer_name"],
            "order_amount": order_amount,
            "purpose": data["purpose"],
            "product": "UPI",
            "merchant_ref_id": merchant.name,
            "remark": data.get("remark", ""),
            "client_ref_id": data["clientRefId"],
            "integration_id": processor.name,
            "tax": tax,
            "fee": fee,
            "transaction_amount": total_amount
        }).insert(ignore_permissions=True)

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
        
        frappe.db.commit()

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
        frappe.log_error("Headers",headers)
        response = requests.post(url, headers = headers, json = payload)
        frappe.log_error("API Response",response.json())
        if response.status_code == 200:
            api_response = response.json()
            data = api_response.get("data",{})
            if not data:
                transaction = frappe.get_doc("Transaction",transaction.name)
                transaction.status = "Failed"
                transaction.remark = "API returning empty json response"
                transaction.save(ignore_permissions = True)
                transaction.submit()
                handle_transaction_failure(order.name,"Cancelled", "Error in upi transaction processing",transaction.name)

            order = frappe.get_doc("Order",order.name)
            order.payment_url = data.get("payment_url","")
            order.success_url = data.get("success_url","")
            order.failed_url = data.get("failed_url","")
            order.close_url = data.get("close_url","")
            order.save(ignore_permissions = True)
            return {
                "message": "Order initialized successfully",
                "payment_url": order.payment_url,
                "success_url": order.success_url,
                "failed_url": order.failed_url,
                "close_url": order.close_url
            }

        else:
            transaction = frappe.get_doc("Transaction",transaction.name)
            transaction.status = "Failed"
            transaction.remark = "API returning empty json response"
            transaction.save(ignore_permissions = True)
            transaction.submit()
            handle_transaction_failure(order.name,"Cancelled", "Error in upi transaction processing",transaction.name)

    
    except Exception as e:
        frappe.log_error("Error in upi initilization",str(e))
        return {
            "Error in upi initilization"
        }



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
        balance = float(wallet_row[0]["balance"])
        # Apply balance change safely
        new_balance = float(wallet_row[0]["balance"]) + float(doc.transaction_amount)

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

        frappe.db.sql("""
            UPDATE `tabWallet`
            SET balance = %s
            WHERE name = %s
        """, (new_balance, doc.merchant_ref_id))
                
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
        frappe.log_error("Error",refund_error)
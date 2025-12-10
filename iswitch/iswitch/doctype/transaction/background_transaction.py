import frappe

@frappe.whitelist()
def process_transaction(transaction_name):
    """
    Background job function to process transaction - following HRMS pattern
    """
    try:
        doc = frappe.get_doc("Transaction", transaction_name)
        
        if doc.status == "Processing":
            processor = frappe.get_doc("Integration", doc.integration)
            order = frappe.get_doc("Order", doc.order)
            status = ""
            remark = ""
            utr = ""
            order_id = ""
            
            if processor.name == "Flipopay":
                headers = {
                    "X-Secret-Key": processor.get_password("secret_key")
                }
                payload = {
                    "transactionAmount": str(order.order_amount),
                    "beneficiaryName": order.customer_name,
                    "beneficiaryEmail": "satsoftwareprivatelimited@gmail.com",
                    "beneficiaryPhoneNumber": "9999999999",
                    "transactionType": order.product,
                    "destinationBank": order.bank,
                    "beneficiaryAccountNumber": order.customer_account_number,
                    "beneficiaryLocation": "Delhi",
                    "beneficiaryIfsc": order.ifsc,
                    "userId": 100041,
                    "orgId": 100041,
                    "reference": doc.order,
                    "affiliateId": 10001,
                    "clientDescription": "Payout Flipopay"
                }

                url = processor.api_endpoint
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                frappe.log_error("API Response", response.json())
                
                if response.status_code != 200 or not response.json():
                    status = "Failed"
                    remark = f"Flipopay API is responding with {response.status_code} status"
                else:
                    try:
                        api_response1 = response.json()
                        api_response = api_response1.get("FundTransfer", {})
                    except Exception as e:
                        remark = "Invalid or empty JSON response from Flipopay API"

                    order_id = api_response.get("Crn", "")
                    status = api_response.get("TransactionStatus", "").upper()

                    if status == "PENDING":
                        status = "Pending"
                    elif status == "SUCCESS":
                        status = "Success"
                    else:
                        status = "Failed"
                        
            else:  # Swavenpay
                payload = {
                    "clientId": processor.get_password("client_id"),
                    "secretKey": processor.get_password("secret_key"),
                    "number": "9999999999",
                    "amount": str(order.order_amount),
                    "transferMode": order.product,
                    "accountNo": order.customer_account_number,
                    "ifscCode": order.ifsc,
                    "beneficiaryName": order.customer_name,
                    "vpa": "",
                    "clientOrderId": doc.order
                }

                url = processor.api_endpoint.rstrip("/") + "/payout"
                response = requests.post(url, json=payload, timeout=15)

                if response.status_code != 200:
                    status = "Failed"
                    remark = f"Swavenpay API is responding with {response.status_code} status"

                try:
                    api_response = response.json()
                except Exception:
                    remark = "Invalid or empty JSON response from Swavenpay fallback API"

                status_code = api_response.get("statusCode")
                status = {
                    1: "Success",
                    0: "Failed",
                    4: "Reversal"
                }.get(status_code, "Pending")

                order_id = api_response.get('orderId', "")
                utr = api_response.get("utr", "")
            
            # Update transaction
            doc.payment_gateway_transaction_id = order_id
            doc.status = status
            doc.utr = utr
            doc.remark = remark
            doc.save(ignore_permissions=True)
            frappe.db.commit()

            # Update order
            frappe.db.set_value("Order", doc.order, 'status', 'processed')
            frappe.db.commit()
        
        elif doc.status == "Failed":
            doc.submit()
            order = frappe.get_doc("Order", doc.order)
            handle_transaction_failure(order, "Transaction failed")
            frappe.db.commit()

        elif doc.status == "Success" and doc.product != "FEES AND CHARGES":
            order = frappe.get_doc("Order", doc.order)
            tax_and_fee = order.transaction_amount - order.order_amount

            transaction = frappe.get_doc({
                "doctype": 'Transaction',
                "order": order.name,
                "merchant": order.merchant_ref_id,
                "amount": tax_and_fee,
                "integration": order.integration_id,
                "product": "FEES AND CHARGES",
                "status": "Success",
                "transaction_type": "Debit"
            }).insert(ignore_permissions=True)
            transaction.submit()
            doc.submit()
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error("Error in transaction processing", str(e))

def handle_transaction_failure(doc, error_message):
    """
    Common function to handle transaction failures and refund wallet
    """
    try:
        # Update order status
        frappe.db.set_value("Order", doc.name, {
            'status': 'cancelled',
            'failed_message': error_message[:100],
            'failed_at': frappe.utils.now()
        })
        
        # Refund merchant wallet
        balance = frappe.db.get_value("Wallet", doc.merchant_ref_id, 'balance')
        frappe.db.set_value("Wallet", doc.merchant_ref_id, 'balance', 
                           float(balance) + float(doc.transaction_amount))
        
        # Refund Xettle Wallet
        wallet = frappe.get_single("Xettle Wallet")
        frappe.db.set_value("Xettle Wallet", None, "tax", 
                           float(wallet.tax) - float(doc.tax))
        frappe.db.set_value("Xettle Wallet", None, "fee", 
                           float(wallet.fee) - float(doc.fee))
        
        frappe.db.commit()

    except Exception as refund_error: 
        frappe.log_error("Error in transaction failure handling", str(refund_error))

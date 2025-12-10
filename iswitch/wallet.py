import frappe
import requests

@frappe.whitelist(allow_guest=True)
def recharge_wallet():
    frappe.db.savepoint("wallet_process")
    try:
        data = frappe.request.get_json()

        account_number = data.get("account_number", "")
        amount = data.get("amount", 0)
        utr = data.get("utr", "")
        remitter_name = data.get("remitter_name","")
        remitter_ifsc_code = data.get("remitter_ifsc_code", "")
        remitter_account_number = data.get("remitter_account_number", "")
        transaction_type = data.get("transaction_type","Credit")

        if not frappe.db.exists("Virtual Account", account_number):
            frappe.log_error(f"There is no such virtual account: {account_number}", "Recharge Wallet Error")
            return

        merchant = frappe.db.get_value("Virtual Account", account_number, 'merchant')
        frappe.set_user(merchant)
        
        if not frappe.db.exists("Virtual Account Logs",{"utr":utr}):
            va_logs = frappe.get_doc({
                "doctype": 'Virtual Account Logs',
                "account_number": account_number,
                "transaction_type": transaction_type,
                "amount": float(amount),
                "utr": utr,
                "remitter_name": remitter_name,
                "remitter_ifsc_code": remitter_ifsc_code,
                "remitter_account_number": remitter_account_number,
                "status": "Success"
            }).insert(ignore_permissions=True)
            return {"status": "success", "message": "Wallet recharge initiated."}
            
        return {"status": "error", "message": "Duplicate UTR. Transaction already processed."}

    except Exception as e:
        frappe.db.rollback(save_point = "wallet_process")
        frappe.log_error(frappe.get_traceback(), "Error in wallet recharge")
        return {"status": "failed", "message": "An error occurred while recharging wallet."}


@frappe.whitelist()
def get_wallet_balance():
    wallet = {}
    try:
        integrations = frappe.db.get_list('Integration', pluck='name')
        
        for integration in integrations:
            processor = frappe.get_doc("Integration", integration)

            if integration == "Nimblepe":
                try:
                    headers = {
                        "APITOKEN": processor.get_password("secret_key")
                    }
                    url = processor.api_endpoint.rstrip("/") + "/merchants/get/account_getbalance"
                    response = requests.get(url, headers=headers,timeout = 5)
                    
                    if response.status_code == 200:
                        api_response = response.json()
                        wallet["Nimblepe"] = api_response.get("balance")
                except Exception as e:
                    frappe.log_error("Error in Nimblepe Balance fetching",str(e))

            elif integration == "Swavenpay":
                payload = {
                    "clientId": processor.get_password("client_id"),
                    "secretKey": processor.get_password("secret_key")
                }
                url = processor.api_endpoint.rstrip("/") + "/balance"
                api_response = {}
                try:
                    response = requests.post(url, json=payload,timeout=5)
                    api_response = response.json()
                except Exception as e:
                    frappe.log_error("Error in swavenpay balance fetching", str(e))
                
                if api_response.get("statusCode") == 1:
                    wallet["Swavenpay"] = api_response.get("balance")

            elif integration == "Ketlapay":
                url = processor.api_endpoint.rstrip("/") + "/balance"
                api_response = {}
                try:
                    headers = {
                        "merchantID": processor.get_password("client_id"),
                        "secretKey": processor.get_password("secret_key")
                    }
                    response = requests.get(url, headers=headers,timeout=5)
                    api_response = response.json()
                    
                except Exception as e:
                    frappe.log_error("Error in ketlapay balance fetching", str(e))

                if api_response.get("success"):
                    wallet["Ketlapay"] = api_response.get("data",{}).get("currentBalance",0)
            
            elif integration == "Toshani":
                payload = {
                    "secretKey": processor.get_password("secret_key")
                }
                url = processor.api_endpoint.rstrip("/") + "/balanceCheck"
                api_response = {}
                try:
                    response = requests.get(url, json=payload,timeout=5)
                    api_response = response.json()
                    
                except Exception as e:
                    frappe.log_error("Error in toshani balance fetching", str(e))

                if api_response.get("success"):
                    api_data = api_response.get("data",{})
                    wallet_balance = api_data.get("Credit_Wallet_Balance",0) - api_data.get("Debit_Wallet_Balance",0)
                    wallet["Toshani"] = wallet_balance
                    
        frappe.log_error("Wallet Balance",wallet)
        return wallet

    except Exception as e:
        frappe.log_error("Error in wallet balance fetching", frappe.get_traceback())
        return {"error": "Error in wallet balance fetching"}
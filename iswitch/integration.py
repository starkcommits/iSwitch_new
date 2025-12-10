import frappe
import requests

@frappe.whitelist()
def get_flipoppay_balance():
    try:
        processor = frappe.get_doc("Integration","Flipopay")
        headers = {
            "X-Secret-Key": processor.get_password("secret_key")
        }
        params = {
            "van": "F9993102510040980"
        }
        url = processor.api_endpoint.rstrip("/") + "/wallet/10040/balance"
        
        response = requests.get(url, headers = headers, params = params)
        if response.status_code == 200:
            api_response = response.json()
            return {
                "processor": processor.name,
                "balance": api_response.get("data")[0]["walletBalance"]
            }

    except Exception as e:
        frappe.log_error("Error in balance fetching", str(e))

@frappe.whitelist()
def get_nimblepe_balance():
    try:
        processor = frappe.get_doc("Integration","Nimblepe")

        headers = {
            "APITOKEN": processor.get_password("secret_key")
        }
        url = processor.api_endpoint.rstrip("/") + "/merchants/get/account_getbalance"

        response = requests.get(url, headers = headers)

        api_response = response.json()

        return {
            "processor": processor.name,
            "balance": api_response.get("balance")
        }

    except Exception as e:
        frappe.log_error("Error in balance fetching",str(e))

@frappe.whitelist()
def get_swavenpay_balance():
    try:
        processor = frappe.get_doc("Integration","Swavenpay")
        payload = {
            "clientId": processor.get_password("client_id"),
            "secretKey": processor.get_password("secret_key")
        }
        url = processor.api_endpoint.rstrip("/") + "/balance"

        response = requests.get(url, json = payload)
        if response.status_code == 200:
            api_response = response.json()
            return {
                "processor": processor.name,
                "balance": api_response.("balance")
            }
        else:
            frappe.throw(f"API response {response.status_code}")
        
    except Exception as e:
        frappe.log_error("Error in balance fetching",str(e))

        











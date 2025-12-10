import frappe
import base64
import os
import json
import requests
from frappe.auth import LoginManager
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from frappe.utils import validate_email_address, getdate, today, get_formatted_email, now, now_datetime, format_datetime

class JSONEncryptionDecryption:
    
    ENCODING_CHARSET = "UTF-8"
    
    @staticmethod
    def encrypt_json(json_data, password):
        try:
            # Convert to JSON string if it's a dict or list
            if isinstance(json_data, (dict, list)):
                json_string = json.dumps(json_data, separators=(',', ':'))
            elif isinstance(json_data, str):
                # Validate if it's valid JSON
                json.loads(json_data)  # This will raise exception if invalid JSON
                json_string = json_data
            else:
                raise ValueError("Input must be a JSON string, dictionary, or list")
            
            result = ""
            TAG_LENGTH_BIT = 128
            IV_LENGTH_BYTE = 16
            SALT_LENGTH_BYTE = 16
            iteration_count = 65536
            key_length = 256
            
            # Generate random IV and salt
            iv = JSONEncryptionDecryption.get_random_nonce(IV_LENGTH_BYTE)
            salt = JSONEncryptionDecryption.get_random_nonce(SALT_LENGTH_BYTE)
            
            # Generate secret key from password
            aes_key_from_password = JSONEncryptionDecryption.get_aes_key_from_password(
                password, salt, iteration_count, key_length
            )
            
            # Create cipher instance
            cipher = Cipher(
                algorithms.AES(aes_key_from_password),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt the JSON string
            cipher_text = encryptor.update(json_string.encode(JSONEncryptionDecryption.ENCODING_CHARSET))
            encryptor.finalize()
            
            # Get the authentication tag
            tag = encryptor.tag
            
            # Combine IV + ciphertext + tag + salt
            cipher_text_with_iv_salt = iv + cipher_text + tag + salt
            result = base64.b64encode(cipher_text_with_iv_salt).decode(JSONEncryptionDecryption.ENCODING_CHARSET)
            
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {str(e)}")
            raise Exception("Invalid JSON format")
        except Exception as e:
            print(f"Error during encryption: {str(e)}")
            raise Exception("Encryption failed")
            
        return result
    
    @staticmethod
    def decrypt_json(encrypted_data, password, return_as_dict=True):
        try:
            result = ""
            TAG_LENGTH_BIT = 128
            IV_LENGTH_BYTE = 16
            SALT_LENGTH_BYTE = 16
            TAG_LENGTH_BYTE = 16
            iteration_count = 65536
            key_length = 256
            
            # Decode base64
            decode = base64.b64decode(encrypted_data.encode(JSONEncryptionDecryption.ENCODING_CHARSET))
            
            # Extract IV, ciphertext, tag, and salt
            iv = decode[:IV_LENGTH_BYTE]
            cipher_text = decode[IV_LENGTH_BYTE:-TAG_LENGTH_BYTE-SALT_LENGTH_BYTE]
            tag = decode[-TAG_LENGTH_BYTE-SALT_LENGTH_BYTE:-SALT_LENGTH_BYTE]
            salt = decode[-SALT_LENGTH_BYTE:]
            
            # Generate secret key from password
            aes_key_from_password = JSONEncryptionDecryption.get_aes_key_from_password(
                password, salt, iteration_count, key_length
            )
            
            # Create cipher instance
            cipher = Cipher(
                algorithms.AES(aes_key_from_password),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt the text
            plain_text = decryptor.update(cipher_text)
            decryptor.finalize()
            
            json_string = plain_text.decode(JSONEncryptionDecryption.ENCODING_CHARSET)
            
            # Return as parsed JSON object or string
            if return_as_dict:
                result = json.loads(json_string)
            else:
                result = json_string
            
        except json.JSONDecodeError as e:
            print(f"Decrypted data is not valid JSON: {str(e)}")
            raise Exception("Decrypted data is not valid JSON")
        except Exception as e:
            print(f"Error during decryption: {str(e)}")
            raise Exception("Decryption failed")
            
        return result
    
    @staticmethod
    def get_aes_key_from_password(password, salt, iteration_count, key_length_bits):
        """
        Generate AES key from password using PBKDF2 with HMAC-SHA256
        """
        try:
            key_length_bytes = key_length_bits // 8
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=key_length_bytes,
                salt=salt,
                iterations=iteration_count,
                backend=default_backend()
            )
            
            key = kdf.derive(password.encode(JSONEncryptionDecryption.ENCODING_CHARSET))
            return key
            
        except Exception as e:
            print(f"Error generating key: {str(e)}")
            raise Exception("Key generation failed")
    
    @staticmethod
    def get_random_nonce(num_bytes):
        """
        Generate random nonce of specified length
        """
        return os.urandom(num_bytes)


@frappe.whitelist()
def bank_onboard():
    try:
        data = frappe.request.get_json()
        if not data:
            return {
                "message":"No request data found"
            }
        
        required_fields = ['bank_name', 'bank_email', 'password']
        for field in required_fields:
            if not data.get(field):
                return {
                    "code": "0x0203",
                    "status": "MISSING_PARAMETER",
                    "message": f"Missing field {field}"
                }
        
        user = frappe.new_doc("User")
        user.email = data.get("bank_email")
        user.first_name = data.get("bank_name")
        user.enabled = 1
        user.new_password = data.get("password")
        user.user_type = "System User"
        user.insert(ignore_permissions=True)

        frappe.local.response.update({
            "status": "Registration Successful",
            "message": {
                "usr": f"{user.name}",
                "pwd": f"{data.get('password')}"
            }
        })

    except Exception as e:
        frappe.db.rollback()
        frappe.local.response.update({
            "code": "0x0500",
            "status": "ERROR",
            "message": f"Registration failed: {str(e)}"
        })

@frappe.whitelist(allow_guest = True)
def bank_login():

    data = frappe.request.get_json()

    config = frappe.get_single("Global Config")
    passphrase = config.get_password("passphrase")

    current_time = now_datetime()
    msgtime = format_datetime(current_time, "yyyy-MM-dd HH:mm:ss.fff")

    bank_req = frappe.new_doc("Bank ReqRes")
    bank_req.request = data
    bank_req.msgid = data.get("msgid")

    if frappe.db.exists("Bank ReqRes",{"msgid":data.get("msgid")}):
        response = {
            "msgid": data.get("msgid"),
            "channelName": "iSwitch",
            "status": "01",
            "errorMsg": "Duplicate transaction not allowed."
        }
        
        frappe.log_error("Response", response)
        encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
        bank_req.response = {"resdata":encrypted_response}
        bank_req.remark = "Duplicate msgId"
        bank_req.save(ignore_permissions = True)
        bank_req.submit()

        return encrypted_response

    bank_req.save(ignore_permissions = True)

    try:
        encrypted_data = data.get("reqdata")
        msgid = data.get("msgid")
    
        decrypted_json = JSONEncryptionDecryption.decrypt_json(encrypted_data, passphrase, return_as_dict=True)
    
        request_type = decrypted_json.get("requestType")
        request_data = decrypted_json.get("data", {})
        username = request_data.get("username","")
        password = request_data.get("password", "")
        if not username or not password:
            response = {
                "msgtime": msgtime,
                "msgid": msgid,
                "channelName": "iSwitch",
                "http_statusCode": 401,
                "status": "01",
                "errorMsg": "Missing username or password"
            }
            frappe.log_error("Response", response)
            encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
            
            bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
            bank_req.response = {"resdata":encrypted_response}
            bank_req.remark = "Missing username or password"

            bank_req.save(ignore_permissions = True)
                
            bank_req.submit()

            return encrypted_response
        
        if not frappe.db.exists("User",{"email":username}):
            response = {
                "msgtime": msgtime,
                "msgid": msgid,
                "channelName": "iSwitch",
                "http_statusCode": 401,
                "status": "01",
                "errorMsg": "User not found"
            }
            frappe.log_error("Response", response)
            encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
            
            bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
            bank_req.response = {"resdata":encrypted_response}
            bank_req.remark = "User not found"
            
            bank_req.save(ignore_permissions = True)
                
            bank_req.submit()

            return encrypted_response

        # Authenticate
        login_manager = LoginManager()
        login_manager.authenticate(user=username, pwd=password)   

        user_doc = frappe.get_doc("User", username)

        user_doc.api_key = frappe.generate_hash(length=15)
        raw = frappe.generate_hash(length=30)
        user_doc.api_secret = raw
        user_doc.save(ignore_permissions=True)
        frappe.db.commit()

        token_string = f"{user_doc.api_key}:{raw}"
        token = base64.b64encode(token_string.encode()).decode()
        current_time = now_datetime()
        msgtime = format_datetime(current_time, "yyyy-MM-dd HH:mm:ss.fff")

        # Return encrypted response
        response = {
            "data": {
                "token": token
            },
            "msgtime": msgtime,
            "msgid": msgid,
            "channelName": "iSwitch",
            "status": "00"
        }
        frappe.log_error("Response", response)
        encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
        bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
        bank_req.response = {"resdata":encrypted_response}
        bank_req.remark = "Logged In"
        
        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()

        return encrypted_response

    except frappe.AuthenticationError as e:
        frappe.log_error("Error in authentication", str(e))

        data = frappe.request.get_json()
        msgId = data.get("msgid")
        
        current_time = now_datetime()
        msgtime = format_datetime(current_time, "yyyy-MM-dd HH:mm:ss.fff")
        response = {
            "msgtime": msgtime,
            "msgid": msgId,
            "channelName": "iSwitch",
            "http_statusCode": 401,
            "status": "01",
            "errorMsg": "Incorrect Password"
        }
        frappe.log_error("Response", response)
        encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
        bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
        bank_req.response = {"resdata":encrypted_response}
        bank_req.remark = "Technical Error"

        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()

        return encrypted_response

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "iSwitch API Error")

        data = frappe.request.get_json()
        msgId = data.get("msgid")
        
        current_time = now_datetime()
        msgtime = format_datetime(current_time, "yyyy-MM-dd HH:mm:ss.fff")
        response = {
            "msgtime": msgtime,
            "msgid": msgId,
            "channelName": "iSwitch",
            "http_statusCode": 401,
            "status": "01",
            "errorMsg": "Technical Error"
        }
        frappe.log_error("Response", response)
        encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
        bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
        bank_req.response = {"resdata":encrypted_response}
        bank_req.remark = "Technical Error"

        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()

        return encrypted_response


@frappe.whitelist(allow_guest = True)
def test_encrypt():
    try:
        data = frappe.request.get_json()
        
        config = frappe.get_single("Global Config")
        passphrase = config.get_password("passphrase")
        
        encrypted_response = JSONEncryptionDecryption.encrypt_json(data, passphrase)
        return encrypted_response
    except Exception as e:
        frappe.throw("Error in encryption", str(e))

@frappe.whitelist(allow_guest = True)
def test_decryption():
    try:
        data = frappe.request.get_json()
        
        config = frappe.get_single("Global Config")
        passphrase = config.get_password("passphrase")
        encrypted_data = data.get("reqData","")
        
        decrypted_response = JSONEncryptionDecryption.decrypt_json(encrypted_data, passphrase, return_as_dict=True)
        return decrypted_response
    except Exception as e:
        frappe.throw("Error in encryption", str(e))


@frappe.whitelist(allow_guest=True)
def bank_webhook():

    auth_header = frappe.request.headers.get('X-Bank-Auth')
    
    data = frappe.request.get_json()
    config = frappe.get_single("Global Config")
    passphrase = config.get_password("passphrase")

    bank_req = frappe.new_doc("Bank ReqRes")
    msgid = data.get("msgId")
    
    if not auth_header or not auth_header.lower().startswith("bearer "):
        error_response = {
            "inwardCreditUpdateResp": {
                "status": "F",
                "errorCode": "401",
                "errorMsg": "X-Bank-Auth headers are missing"
            }
        }
        
        encrypted_response = JSONEncryptionDecryption.encrypt_json(error_response, passphrase)
            
        res = {
            "respData": encrypted_response,
            "msgId": msgid
        }
        
        bank_req.request = data
        bank_req.response = res
        bank_req.remark = "X-Bank-Auth headers are missing"
        bank_req.msgid = msgid
        
        
        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()
        
        return res
    
    encoded = auth_header[6:].strip()

    decoded_bytes = base64.b64decode(encoded)
    decoded_str = decoded_bytes.decode()
    
    api_key, raw = decoded_str.split(":", 1)
    if not frappe.db.exists("User",{"api_key":api_key}):
        error_response = {
            "inwardCreditUpdateResp": {
                "status": "F",
                "errorCode": "401",
                "errorMsg": "Invalid token"
            }
        }
        
        encrypted_response = JSONEncryptionDecryption.encrypt_json(error_response, passphrase)
            
        res = {
            "respData": encrypted_response,
            "msgId": msgid
        }
        
        
        bank_req.request = data
        bank_req.response = res
        bank_req.remark = "Invalid token"
        bank_req.msgid = msgid
        
        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()
        
        return res
    

    if frappe.db.exists("Bank ReqRes",{"msgid":msgid}):
        error_response = {
            "inwardCreditUpdateResp": {
                "status": "F",
                "errorCode": "401",
                "errorMsg": "Duplicate msgId"
            }
        }
        
        encrypted_response = JSONEncryptionDecryption.encrypt_json(error_response, passphrase)
            
        res = {
            "respData": encrypted_response,
            "msgId": msgid
        }
        
        
        bank_req.request = data
        bank_req.response = res
        bank_req.remark = "Duplicate msgId"
        bank_req.msgid = msgid
        
        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()
        
        return res

    bank_req.request = data

    bank_req.save(ignore_permissions = True)

    try:

        encrypted_data = data.get("reqData")

        decrypted_json = JSONEncryptionDecryption.decrypt_json(encrypted_data, passphrase, return_as_dict=True)
        
        req_data = decrypted_json.get("inwardCreditUpdateReq", {})
        
        utr = req_data.get("txnRefNo", "")
        account_number = req_data.get("VANum", "")
        amt = req_data.get("txnAmt", "")
        remitterName = req_data.get("remitterName", "")
        remitterAccNo = req_data.get("remitterAccNo", "")
        remitterBankIFSC = req_data.get("remitterBankIFSC", "")

        if not frappe.db.exists("Virtual Account", {"account_number":account_number}):
            response = {
                "inwardCreditUpdateResp": {
                    "status": "F",
                    "errorCode": "004",
                    "errorMsg": "Virtual Account Not Found"
                }
            }
            encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
            res = {
                "respData": encrypted_response,
                "msgId": msgid
            }
            bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
            bank_req.response = res
            bank_req.remark = "Virtual Account Not Found"
            
            bank_req.save(ignore_permissions = True)
                
            bank_req.submit()
            
            return res


        merchant = frappe.db.get_value("Virtual Account", account_number, 'merchant')
        frappe.set_user(merchant)
        
        if not frappe.db.exists("Virtual Account Logs", {"utr": utr}):
            va_logs = frappe.get_doc({
                "doctype": 'Virtual Account Logs',
                "account_number": account_number,
                "transaction_type": "Credit",
                "amount": float(amt),
                "utr": utr,
                "status": "Success"
            }).insert(ignore_permissions=True)
            
            response = {
                "inwardCreditUpdateResp": {
                    "status": "S",
                    "errorCode": "000",
                    "errorMsg": "Success"
                }
            }
            
            encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
            
            res = {
                "respData": encrypted_response,
                "msgId": msgid
            }

            bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
            bank_req.response = res
            
            bank_req.save(ignore_permissions = True)
                
            bank_req.submit()

            return res
            
        # If UTR already exists, return failure
        response = {
            "inwardCreditUpdateResp": {
                "status": "F",
                "errorCode": "004",
                "errorMsg": "Duplicate UTR"
            }
        }
        
        encrypted_response = JSONEncryptionDecryption.encrypt_json(response, passphrase)
        
        res = {
            "respData": encrypted_response,
            "msgId": msgid
        }
        bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
        bank_req.response = res
        bank_req.msgid = msgid
        bank_req.remark = "Duplicate UTR"

        bank_req.save(ignore_permissions = True)
            
        bank_req.submit()
        
        return res
        
    except Exception as e:
        frappe.log_error("Error in bank webhook processing", str(e))
        
        # Return encrypted error response
        try:
            config = frappe.get_single("Global Config")
            passphrase = config.get_password("passphrase")
            
            error_response = {
                "inwardCreditUpdateResp": {
                    "status": "F",
                    "errorCode": "500",
                    "errorMsg": "Internal Server Error"
                }
            }
            
            encrypted_response = JSONEncryptionDecryption.encrypt_json(error_response, passphrase)
            
            res = {
                "respData": encrypted_response,
                "msgId": data.get("msgId", "")
            }
            
            bank_req = frappe.get_doc("Bank ReqRes",bank_req.name)
            bank_req.response = res
            
            bank_req.save(ignore_permissions = True)
                
            bank_req.submit()
            
            return res
        except:
            # Last resort - return unencrypted error
            return {
                "error": "Internal server error",
                "msgId": data.get("msgId", "") if data else ""
            }

@frappe.whitelist()
def bank_access_token():
    try:
        banks = frappe.db.get_list('Bank Config', pluck='name')
        for bank in banks:
            if bank == "Union Bank":
                bank_doc = frappe.get_doc("Bank Config", bank)
                headers = {
                    "Content-Type": "application/json",
                    "apiToken": bank_doc.get_password("api_token")
                }
                data = {
                    "userName": bank_doc.user_name,
                    "grantType": "password",
                    "clientId": bank_doc.client_id,
                    "clientSecret": bank_doc.get_password("client_secret"),
                    "password": bank_doc.get_password("password"),
                    "scope":"offline_access"
                }
                frappe.log_error("Access Token Headers",headers)
                frappe.log_error("Access Token Payload", data)

                config = frappe.get_single("Global Config")
                passphrase = config.get_password("passphrase")
                
                encrypted_response = JSONEncryptionDecryption.encrypt_json(data, passphrase)
                
                payload = {
                    "reqData": encrypted_response
                }
                frappe.log_error("Access Token Encrypted Payload", payload)
                url = "https://apimuatext.unionbankofindia.co.in/cms/OAPI/accessToken"
                api_response = requests.post(url, json = payload, headers = headers)
                response = api_response.json()
                frappe.log_error("Access Token Response",response)
                respData = response.get("respData","")

                decrypted_response = JSONEncryptionDecryption.decrypt_json(respData, passphrase, return_as_dict=True)
                frappe.log_error("Access Token Decrypted Response", decrypted_response)
                access_token = decrypted_response.get("access_token","")
                bank_doc.bearer = access_token
                bank_doc.save(ignore_permissions=True)
                frappe.db.commit()
                return {
                    "Token updated successfully"
                }

    except Exception as e:
        frappe.log_error("Error in getting access token", str(e))
        frappe.throw("Error in getting access token", str(e))
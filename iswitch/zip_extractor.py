# import subprocess
# import pandas as pd
# import json
# import os
# import tempfile
# import shutil
# import frappe
# from frappe.utils import get_site_path
# from frappe.utils.file_manager import get_file_path


# def extract_zip_with_p7zip(zip_path, password="19685"):
#     """Extract ZIP file using p7zip"""
#     temp_dir = tempfile.mkdtemp()
    
#     try:
#         # Try 7z command
#         command = ['7z', 'x', zip_path, f'-o{temp_dir}', f'-p{password}', '-y']
#         result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        
#         if result.returncode != 0:
#             return None
        
#         # Find extracted files
#         extracted_files = []
#         for root, dirs, files in os.walk(temp_dir):
#             for file in files:
#                 if file.lower().endswith(('.xlsx', '.xls', '.csv')):
#                     extracted_files.append(os.path.join(root, file))
        
#         return extracted_files[0] if extracted_files else None
        
#     except Exception as e:
#         frappe.log_error(f"ZIP extraction failed: {str(e)}", "ZIP Processor")
#         return None


# def convert_excel_to_json(excel_file_path):
#     """Convert Excel to JSON with transaction data"""
#     try:
#         # Read Excel file starting from row 8 (header row)
#         df = pd.read_excel(excel_file_path, sheet_name=0, header=7)  # Row 8 = index 7
        
#         # Clean column names
#         df.columns = df.columns.str.strip()
        
#         # Remove empty rows
#         df = df.dropna(how='all')
        
#         # Convert to records
#         records = df.to_dict('records')
        
#         # Clean up records
#         cleaned_records = []
#         for record in records:
#             cleaned_record = {}
#             for key, value in record.items():
#                 if pd.isna(value):
#                     cleaned_record[key] = None
#                 else:
#                     cleaned_record[key] = str(value) if not isinstance(value, (int, float)) else value
#             cleaned_records.append(cleaned_record)
        
#         # Return JSON structure
#         return {
#             'status': 'success',
#             'record_count': len(cleaned_records),
#             'data': cleaned_records
#         }
        
#     except Exception as e:
#         frappe.log_error(f"Excel conversion failed: {str(e)}", "ZIP Processor")
#         return {'status': 'error', 'message': str(e)}


# def process_payin_zip(doc, method, password="19685"):
#     """
#     Process ZIP file attached to Payin document and return JSON data
    
#     Args:
#         payin_doc_name (str): Name of the Payin document
#         password (str): ZIP password
    
#     Returns:
#         dict: JSON data with transaction records
#     """
#     temp_dir = None
    
#     try:
#         # Get Payin document
#         payin_doc = frappe.get_doc("Payin", doc)
        
#         if not payin_doc.file:
#             return {"status": "error", "message": "No file attached"}
        
#         # Get file path
#         if payin_doc.file.startswith('/files/'):
#             file_path = get_site_path() + payin_doc.file
#         else:
#             file_path = get_file_path(payin_doc.file)
        
#         if not os.path.exists(file_path):
#             return {"status": "error", "message": "File not found"}
        
#         # Extract ZIP
#         extracted_file = extract_zip_with_p7zip(file_path, password)
        
#         if not extracted_file:
#             return {"status": "error", "message": "Failed to extract ZIP"}
        
#         # Convert to JSON
#         result = convert_excel_to_json(extracted_file)
        
#         # Clean up
#         if extracted_file and os.path.exists(os.path.dirname(extracted_file)):
#             shutil.rmtree(os.path.dirname(extracted_file))
        
#         frappe.log_error("JSON", result)
        
#     except Exception as e:
#         frappe.log_error(f"Process payin zip error: {str(e)}", "ZIP Processor")
#         return {"status": "error", "message": str(e)}


# # Sample JSON output structure and field mapping
# """
# SAMPLE OUTPUT JSON:
# {
#     "status": "success",
#     "record_count": 2,
#     "data": [
#         {
#             "CUSTOMER CODE": "19685",
#             "PRODUCT CODE": "IMPS",
#             "DEPOSIT BRANCH NAME": null,
#             "DEPOSIT LOCATION NAME": "MUMBAI",
#             "VIRTUAL ACCOUNT NUMBER": "1968591105778",
#             "CLEARING DATE": "15-07-2025",
#             "NUMBER OF INSTRUMENTS": "1",
#             "INSTRUMENT NUMBER": null,
#             "INSTRUMENT DATE": "14-07-2025",
#             "INSTRUMENT DRAWN ON BANK NAME": "UNION BANK OF INDIA(UBI)",
#             "INSTRUMENT AMOUNT": "5",
#             "INST ADDTNL INFO CODE 1": null,
#             "REMITTER BANK NAME": null,
#             "REMITTER IFSC CODE ": "IDFB0009751",
#             "REMITTER NAME": null,
#             "CREDIT DATE": "15-07-2025",
#             "DEPOSIT SLIP AMOUNT": "5",
#             "RETURN MARKING DATE": null,
#             "RETURN REASON NAME": null,
#             "DEP SLIP ADDTNL INFO 1": null,
#             "REMITTER ACCOUNT NUMBER": "10135550195",
#             "CUSTOMER NAME": "SAT SOFTWARE AND INFRASTRUCTURE PRIVATE LIMITED",
#             "UTR NUMBER": "519520450099",
#             "DEPOSIT SLIP NUMBER": "519520450099",
#             "CBS Day Sl": null,
#             "DEPOSIT DATE": "14-07-2025",
#             "ADJUSTED AMOUNT": null,
#             "ADJUSTMENT DATE": null,
#             "ADJUSTMENT": null,
#             "CREDIT AMOUNT": "5",
#             "DRAWER NAME": "KGC INFOTECH PRIVATE",
#             "POOLING RUN SERIAL": "6",
#             "RECOVERED DATE": null
#         }
#     ]
# }

# KEY FIELD MAPPINGS FOR YOUR USE:
# - Customer Code: data[i]["CUSTOMER CODE"]
# - Amount: data[i]["INSTRUMENT AMOUNT"] or data[i]["CREDIT AMOUNT"]  
# - Date: data[i]["CLEARING DATE"] or data[i]["CREDIT DATE"]
# - Reference: data[i]["UTR NUMBER"] or data[i]["INSTRUMENT NUMBER"]
# - Product: data[i]["PRODUCT CODE"] (IMPS, NEFT, etc.)
# - Virtual Account: data[i]["VIRTUAL ACCOUNT NUMBER"]
# - Customer Name: data[i]["CUSTOMER NAME"]
# - Remitter: data[i]["REMITTER NAME"] or data[i]["DRAWER NAME"]
# """

import frappe
import requests
def process_payin_zip(doc,method):
    try:
        payload = {
            "file": f"https://api.iSwitch.in{doc.file}",
            "email": doc.email,
            "creation": doc.creation,
            "modified": doc.modified
        }
        url = "http://13.202.185.148:8083/webhook/payin"

        response = requests.post(url, json = payload)
        if response != 200:
            frappe.log_error("Error in zip extraction api",response.json())
        
    except Exception as e:
        frappe.log_error("Error in zip extraction api call", str(e))
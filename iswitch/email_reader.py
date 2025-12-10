import imaplib
import email
from email.header import decode_header
import os
import re
import frappe
from frappe.utils.file_manager import save_file
import tempfile

class ScheduledGmailProcessor:
    def __init__(self):
        gmail_config = frappe.get_doc("Gmail Config","Gmail Config")
        
        self.email_address = gmail_config.email
        self.password = gmail_config.get_password("app_password")
        self.sender_email = gmail_config.sender_email
        self.imap = None
    
    def connect(self):
        """Connect to Gmail IMAP server"""
        try:
            if not self.email_address or not self.password:
                frappe.log_error("Gmail credentials not configured in Gmail Config doctype", "Gmail Processor")
                return False
                
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.imap.login(self.email_address, self.password)
            frappe.logger().info(f"Gmail connected successfully for {self.email_address}")
            return True
            
        except Exception as e:
            frappe.log_error(f"Gmail connection failed: {str(e)}", "Gmail Processor")
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
    
    def decode_mime_words(self, s):
        """Decode MIME encoded words in headers"""
        if not s:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(s):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8'))
                except:
                    decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(part)
        
        return ''.join(decoded_parts)
    
    def extract_sender_email(self, sender_header):
        """Extract just the email address from sender header"""
        email_pattern = r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(email_pattern, sender_header)
        if match:
            return match.group(1) or match.group(2)
        return sender_header.strip()
    
    def check_duplicate_payin(self, sender_email, filename):
        """Check if Payin document already exists for this sender and file"""
        try:
            existing = frappe.db.exists("Payin", {
                "email": sender_email,
                "file": f"/private/files/{filename}"
            })
            return existing
        except:
            return None
    
    def create_payin_document(self, sender_email, file_data, filename, email_subject=""):
        """Create a new Payin document with attachment"""
        try:
            sender_clean = self.extract_sender_email(sender_email)
            
            # Check for duplicates
            if self.check_duplicate_payin(sender_clean, filename):
                frappe.logger().info(f"Payin document already exists for {filename} from {sender_clean}")
                return None
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            try:
                # Create new Payin document
                payin_doc = frappe.new_doc("Payin")
                payin_doc.email = sender_clean
                
                # Save document first to get a name
                payin_doc.insert()
                
                # Save file using Frappe's file manager
                file_doc = save_file(
                    fname=filename,
                    content=file_data,
                    dt="Payin",
                    dn=payin_doc.name,
                    is_private=0
                )
                
                # Update the file field
                payin_doc.file = file_doc.file_url
                payin_doc.save()
                payin_doc.submit()
                frappe.db.commit()
                
                frappe.logger().info(f"Created Payin document: {payin_doc.name} for {filename}")
                return payin_doc.name
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            frappe.log_error(f"Error creating Payin document: {str(e)}", "Gmail Processor")
            return None
    
    def process_attachments(self, msg, sender_email, subject=""):
        """Process attachments and create Payin documents for ZIP files"""
        processed_files = []
        
        if not msg.is_multipart():
            return processed_files
        
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if not filename:
                continue
            
            filename = self.decode_mime_words(filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Only process ZIP files
            if file_ext != '.zip':
                continue
            
            try:
                file_data = part.get_payload(decode=True)
                if not file_data:
                    continue
                
                # Create Payin document
                payin_doc_name = self.create_payin_document(
                    sender_email, 
                    file_data, 
                    filename, 
                    subject
                )
                
                if payin_doc_name:
                    processed_files.append({
                        'filename': filename,
                        'size': len(file_data),
                        'payin_doc': payin_doc_name
                    })
                    
            except Exception as e:
                frappe.log_error(f"Error processing attachment {filename}: {str(e)}", "Gmail Processor")
        
        return processed_files
    
    def mark_as_read(self, message_id):
        """Mark email as read"""
        try:
            self.imap.store(message_id, '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            frappe.log_error(f"Error marking email as read: {str(e)}", "Gmail Processor")
            return False
    
    def process_unread_emails(self):
        """Main processing function - processes unread emails from target sender"""
        if not self.sender_email:
            frappe.log_error("Target sender email not configured", "Gmail Processor")
            return {"status": "error", "message": "Target sender email not configured"}
        
        if not self.connect():
            return {"status": "error", "message": "Failed to connect to Gmail"}
        
        try:
            # Select INBOX
            self.imap.select("INBOX")
            
            # Search for unread emails from specific sender
            search_criteria = f'FROM "{self.sender_email}" UNSEEN'
            status, messages = self.imap.search(None, search_criteria)
            
            if status != 'OK':
                return {"status": "error", "message": "Failed to search emails"}
            
            message_ids = messages[0].split()
            
            if not message_ids:
                frappe.logger().info(f"No new unread emails from {self.sender_email}")
                return {"status": "success", "message": "No new emails to process", "processed": 0}
            
            processed_count = 0
            total_files = 0
            
            frappe.logger().info(f"Processing {len(message_ids)} unread emails from {self.sender_email}")
            
            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = self.imap.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = self.decode_mime_words(msg.get("Subject", "No Subject"))
                    sender = self.decode_mime_words(msg.get("From", "Unknown Sender"))
                        
                    # Process attachments
                    files_processed = self.process_attachments(msg, sender, subject)
                    
                    if files_processed:
                        total_files += len(files_processed)
                        frappe.logger().info(f"Processed {len(files_processed)} files from email: {subject}")
                        
                        # Mark email as read only if we successfully processed files
                        self.mark_as_read(msg_id)
                        processed_count += 1
                    
                    # Commit after each email to avoid losing progress
                    frappe.db.commit()
                    
                except Exception as e:
                    frappe.log_error(f"Error processing email {msg_id.decode()}: {str(e)}", "Gmail Processor")
                    # Don't mark as read if there was an error
                    continue
            
            result = {
                "status": "success",
                "message": f"Processed {processed_count} emails with {total_files} ZIP files",
                "processed": processed_count,
                "files": total_files
            }
            
            frappe.logger().info(f"Gmail processing completed: {result['message']}")
            return result
            
        except Exception as e:
            frappe.log_error(f"Gmail processing error: {str(e)}", "Gmail Processor")
            return {"status": "error", "message": str(e)}
        
        finally:
            self.disconnect()

@frappe.whitelist(allow_guest=True)
def process_gmail_emails():
    """
    Whitelisted function to process Gmail emails
    This function should be called by Frappe scheduler every hour
    """
    try:
        frappe.set_user("Administrator")
        processor = ScheduledGmailProcessor()
        result = processor.process_unread_emails()
        
        # Log the result
        if result["status"] == "success":
            frappe.log_error(f"Gmail scheduler: {result['message']}")
        else:
            frappe.logger().error(f"Gmail scheduler error: {result['message']}")
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Gmail scheduler critical error: {str(e)}", "Gmail Scheduler")
        return {"status": "error", "message": str(e)}

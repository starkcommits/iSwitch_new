import frappe
from frappe.model.document import Document

class VirtualAccountLogs(Document):
    def after_insert(self):
        try:
            if self.status == "Success" and self.docstatus == 0:
                merchant = frappe.db.get_value("Virtual Account", self.account_number, 'merchant')

                wallet_row = frappe.db.sql("""
                    SELECT balance FROM `tabWallet`
                    WHERE name = %s FOR UPDATE
                """, (merchant,), as_dict=True)

                if not wallet_row:
                    frappe.throw("Wallet not found for the merchant.")

                balance = float(wallet_row[0].balance or 0.0)
                
                new_balance = balance + float(self.amount)
                if self.transaction_type == "Debit":
                    new_balance = balance - float(self.amount)
                    
                frappe.db.sql("""
                    UPDATE `tabWallet`
                    SET balance = %s
                    WHERE name = %s
                """, (new_balance, merchant))

                self.opening_balance = balance
                self.closing_balance = new_balance
                self.db_set("opening_balance", balance)
                self.db_set("closing_balance", new_balance)
                self.save()
                self.submit()

            elif self.status == "Failed" and self.docstatus == 0:
                # self.save()
                self.submit()

        except Exception as e:
            frappe.db.rollback(save_point = "wallet_process")
            frappe.log_error("Error in van processing",str(e))

# Copyright (c) 2025, Xettle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Adjustment(Document):
	def after_insert(self):
		main_balance = frappe.db.get_value("Wallet", self.merchant_id, 'balance') or 0
		lean_balance = frappe.db.get_value("Lean Wallet", self.merchant_id, 'balance') or 0

		if self.to == 'Main':
			if lean_balance < self.amount:
				frappe.msgprint("Lean wallet doesn't have this much money")
				self.status = 'Failed'
				frappe.db.commit()  # Ensure the insert is fully committed before submit
				doc = frappe.get_doc(self.doctype, self.name)
				doc.submit()
				return
			frappe.db.set_value("Wallet", self.merchant_id, 'balance', main_balance + self.amount)
			frappe.db.set_value("Lean Wallet", self.merchant_id, 'balance', lean_balance - self.amount)
			self.status = 'Success'
			frappe.db.commit()  # Ensure the insert is fully committed before submit
			doc = frappe.get_doc(self.doctype, self.name)
			doc.submit()
		else:
			if main_balance < self.amount:
				frappe.msgprint("Main wallet doesn't have this much money")
				self.status = 'Failed'
				frappe.db.commit()  # Ensure the insert is fully committed before submit
				doc = frappe.get_doc(self.doctype, self.name)
				doc.submit()
				return
			frappe.db.set_value("Wallet", self.merchant_id, 'balance', main_balance - self.amount)
			frappe.db.set_value("Lean Wallet", self.merchant_id, 'balance', lean_balance + self.amount)
			self.status = 'Success'
			frappe.db.commit()  # Ensure the insert is fully committed before submit
			doc = frappe.get_doc(self.doctype, self.name)
			doc.submit()
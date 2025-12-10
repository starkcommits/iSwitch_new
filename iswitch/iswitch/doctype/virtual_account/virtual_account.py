# Copyright (c) 2025, Xettle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import random

class VirtualAccount(Document):
	def before_insert(self):
		if not self.prefix:
			frappe.throw("BIN is required before generating account number.")

		# Generate account number with prefix
		prefix = self.prefix
		remaining_length = 12 - len(prefix)

		if remaining_length <= 0:
			frappe.throw("BIN is too long to generate a 12-digit account number.")
		
		if not self.account_number:
			suffix = ''.join(random.choices('0123456789', k=remaining_length))
			self.account_number = prefix + suffix
		self.owner = self.merchant

		# # Optional: Change current user to merchant (if valid)
		# if self.merchant:
		# 	frappe.set_user(self.merchant)
	pass

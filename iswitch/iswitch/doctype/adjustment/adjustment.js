// Copyright (c) 2025, Xettle and contributors
// For license information, please see license.txt

frappe.ui.form.on('Adjustment', {
    validate: function(frm) {
        // Check if from and to are the same
        if (frm.doc.from === frm.doc.to) {
            frappe.throw(__('From and To cannot be the same.'));
        }

        // Check if amount is negative
        if (frm.doc.amount < 1 ) {
            frappe.throw(__('Amount cannot be less than 1.'));
        }
    }
});

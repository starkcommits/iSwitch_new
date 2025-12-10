// Copyright (c) 2025, Xettle and contributors
// For license information, please see license.txt

frappe.ui.form.on('Merchant', {
    validate: function (frm) {
        const productRanges = {};

        (frm.doc.product_pricing || []).forEach((row, i) => {
            const product = row.product;
            const start = parseFloat(row.start_value);
            const end = parseFloat(row.end_value);

            if (!product || isNaN(start) || isNaN(end)) return;

            if (start >= end) {
                frappe.throw(`Row ${row.idx}: Start Value must be less than End Value`);
            }

            if (!productRanges[product]) {
                productRanges[product] = [];
            }

            // Check for overlap in the same product
            for (let [prevStart, prevEnd, prevIdx] of productRanges[product]) {
                const isOverlapping = !(end <= prevStart || start >= prevEnd);
                if (isOverlapping) {
                    frappe.throw(`Row ${row.idx} conflicts with Row ${prevIdx} for product "${product}". Overlapping ranges.`);
                }
            }

            productRanges[product].push([start, end, row.idx]);
        });
    }
});
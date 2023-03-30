// Copyright (c) 2019, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Event Consumer", {
	refresh: function (frm) {
		// formatter for subscribed doctype approval status
		frm.set_indicator_formatter("status", function (doc) {
			let indicator = "orange";
			if (doc.status == "Approved") {
				indicator = "green";
			} else if (doc.status == "Rejected") {
				indicator = "red";
			}
			return indicator;
		});
	},
});

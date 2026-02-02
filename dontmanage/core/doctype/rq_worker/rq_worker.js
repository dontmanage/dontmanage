// Copyright (c) 2022, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("RQ Worker", {
	refresh: function (frm) {
		// Nothing in this form is supposed to be editable.
		frm.disable_form();
	},
});

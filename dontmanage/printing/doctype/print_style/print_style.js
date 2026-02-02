// Copyright (c) 2017, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Print Style", {
	refresh: function (frm) {
		frm.add_custom_button(__("Print Settings"), () => {
			dontmanage.set_route("Form", "Print Settings");
		});
	},
});

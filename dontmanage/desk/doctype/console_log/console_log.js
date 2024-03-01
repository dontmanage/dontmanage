// Copyright (c) 2020, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Console Log", {
	refresh: function (frm) {
		frm.add_custom_button(__("Re-Run in Console"), () => {
			window.localStorage.setItem("system_console_code", frm.doc.script);
			window.localStorage.setItem("system_console_type", frm.doc.type);
			dontmanage.set_route("Form", "System Console");
		});
	},
});

// Copyright (c) 2025, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Desktop Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Visit Desktop"), () => dontmanage.set_route("desktop"));
	},
});

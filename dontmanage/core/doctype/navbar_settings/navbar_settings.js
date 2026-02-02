// Copyright (c) 2020, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Navbar Settings", {
	after_save: function (frm) {
		dontmanage.ui.toolbar.clear_cache();
	},
});

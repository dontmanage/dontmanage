// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.ui.form.on("Session Default Settings", {
	refresh: function (frm) {
		frm.set_query("ref_doctype", "session_defaults", function () {
			return {
				filters: {
					issingle: 0,
					istable: 0,
				},
			};
		});
	},
});

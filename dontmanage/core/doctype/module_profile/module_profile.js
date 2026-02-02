// Copyright (c) 2020, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Module Profile", {
	refresh: function (frm) {
		if (has_common(dontmanage.user_roles, ["Administrator", "System Manager"])) {
			if (!frm.module_editor && frm.doc.__onload && frm.doc.__onload.all_modules) {
				const module_area = $(frm.fields_dict.module_html.wrapper);
				frm.module_editor = new dontmanage.ModuleEditor(frm, module_area);
			}
		}

		if (frm.module_editor) {
			frm.module_editor.show();
		}
	},

	validate: function (frm) {
		if (frm.module_editor) {
			frm.module_editor.set_modules_in_table();
		}
	},
});

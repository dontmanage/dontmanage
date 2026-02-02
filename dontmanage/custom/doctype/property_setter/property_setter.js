// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.ui.form.on("Property Setter", {
	validate: function (frm) {
		if (frm.doc.property_type == "Check" && !["0", "1"].includes(frm.doc.value)) {
			dontmanage.throw(__("Value for a check field can be either 0 or 1"));
		}
	},
});

// Copyright (c) 2016, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Bulk Update", {
	refresh: function (frm) {
		frm.set_query("document_type", function () {
			return {
				filters: [
					["DocType", "issingle", "=", 0],
					["DocType", "name", "not in", dontmanage.model.core_doctypes_list],
				],
			};
		});

		frm.page.set_primary_action(__("Update"), function () {
			if (!frm.doc.update_value) {
				dontmanage.throw(__('Field "value" is mandatory. Please specify value to be updated'));
			} else {
				dontmanage
					.call({
						method: "dontmanage.desk.doctype.bulk_update.bulk_update.update",
						args: {
							doctype: frm.doc.document_type,
							field: frm.doc.field,
							value: frm.doc.update_value,
							condition: frm.doc.condition,
							limit: frm.doc.limit,
						},
					})
					.then((r) => {
						let failed = r.message;
						if (!failed) failed = [];

						if (failed.length && !r._server_messages) {
							dontmanage.throw(
								__("Cannot update {0}", [
									failed.map((f) => (f.bold ? f.bold() : f)).join(", "),
								])
							);
						} else {
							dontmanage.msgprint({
								title: __("Success"),
								message: __("Updated Successfully"),
								indicator: "green",
							});
						}

						dontmanage.hide_progress();
						frm.save();
					});
			}
		});
	},

	document_type: function (frm) {
		// set field options
		if (!frm.doc.document_type) return;

		dontmanage.model.with_doctype(frm.doc.document_type, function () {
			var options = $.map(dontmanage.get_meta(frm.doc.document_type).fields, function (d) {
				if (d.fieldname && dontmanage.model.no_value_type.indexOf(d.fieldtype) === -1) {
					return d.fieldname;
				}
				return null;
			});
			frm.set_df_property("field", "options", options);
		});
	},
});

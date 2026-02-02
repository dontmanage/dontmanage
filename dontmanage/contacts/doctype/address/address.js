// Copyright (c) 2016, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Address", {
	refresh: function (frm) {
		if (frm.doc.__islocal) {
			const last_doc = dontmanage.contacts.get_last_doc(frm);
			if (
				dontmanage.dynamic_link &&
				dontmanage.dynamic_link.doc &&
				dontmanage.dynamic_link.doc.name == last_doc.docname
			) {
				frm.set_value("links", "");
				frm.add_child("links", {
					link_doctype: dontmanage.dynamic_link.doctype,
					link_name: dontmanage.dynamic_link.doc[dontmanage.dynamic_link.fieldname],
				});
			}
		}
		frm.set_query("link_doctype", "links", function () {
			return {
				query: "dontmanage.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: "HTML",
					fieldname: "address_html",
				},
			};
		});
		frm.refresh_field("links");

		if (frm.doc.links) {
			for (let i in frm.doc.links) {
				let link = frm.doc.links[i];
				frm.add_custom_button(
					__("{0}: {1}", [__(link.link_doctype), __(link.link_name)]),
					function () {
						dontmanage.set_route("Form", link.link_doctype, link.link_name);
					},
					__("Links")
				);
			}
		}
	},
	validate: function (frm) {
		// clear linked customer / supplier / sales partner on saving...
		if (frm.doc.links) {
			frm.doc.links.forEach(function (d) {
				dontmanage.model.remove_from_locals(d.link_doctype, d.link_name);
			});
		}
	},
	after_save: function (frm) {
		dontmanage.run_serially([
			() => dontmanage.timeout(1),
			() => {
				const last_doc = dontmanage.contacts.get_last_doc(frm);
				if (
					dontmanage.dynamic_link &&
					dontmanage.dynamic_link.doc &&
					dontmanage.dynamic_link.doc.name == last_doc.docname
				) {
					for (let i in frm.doc.links) {
						let link = frm.doc.links[i];
						if (
							last_doc.doctype == link.link_doctype &&
							last_doc.docname == link.link_name
						) {
							dontmanage.set_route("Form", last_doc.doctype, last_doc.docname);
						}
					}
				}
			},
		]);
	},
});

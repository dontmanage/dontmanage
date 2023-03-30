// Copyright (c) 2019, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Notification Settings", {
	onload: (frm) => {
		dontmanage.breadcrumbs.add({
			label: __("Settings"),
			route: "#modules/Settings",
			type: "Custom",
		});
		frm.set_query("subscribed_documents", () => {
			return {
				filters: {
					istable: 0,
				},
			};
		});
	},

	refresh: (frm) => {
		if (dontmanage.user.has_role("System Manager")) {
			frm.add_custom_button(__("Go to Notification Settings List"), () => {
				dontmanage.set_route("List", "Notification Settings");
			});
		}
	},
});

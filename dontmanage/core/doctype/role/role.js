// Copyright (c) 2022, DontManage and Contributors
// MIT License. See LICENSE

dontmanage.ui.form.on("Role", {
	refresh: function (frm) {
		if (frm.doc.name === "All") {
			frm.dashboard.add_comment(
				__("Role 'All' will be given to all System Users."),
				"yellow"
			);
		}

		frm.set_df_property("is_custom", "read_only", dontmanage.session.user !== "Administrator");

		frm.add_custom_button("Role Permissions Manager", function () {
			dontmanage.route_options = { role: frm.doc.name };
			dontmanage.set_route("permission-manager");
		});
		frm.add_custom_button("Show Users", function () {
			dontmanage.route_options = { role: frm.doc.name };
			dontmanage.set_route("List", "User", "Report");
		});
	},
});

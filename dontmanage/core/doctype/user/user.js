dontmanage.ui.form.on("User", {
	before_load: function (frm) {
		var update_tz_select = function (user_language) {
			frm.set_df_property("time_zone", "options", [""].concat(dontmanage.all_timezones));
		};

		if (!dontmanage.all_timezones) {
			dontmanage.call({
				method: "dontmanage.core.doctype.user.user.get_timezones",
				callback: function (r) {
					dontmanage.all_timezones = r.message.timezones;
					update_tz_select();
				},
			});
		} else {
			update_tz_select();
		}
	},

	time_zone: function (frm) {
		if (frm.doc.time_zone && frm.doc.time_zone.startsWith("Etc")) {
			frm.set_df_property(
				"time_zone",
				"description",
				__("Note: Etc timezones have their signs reversed.")
			);
		}
	},

	role_profile_name: function (frm) {
		if (frm.doc.role_profile_name) {
			dontmanage.call({
				method: "dontmanage.core.doctype.user.user.get_role_profile",
				args: {
					role_profile: frm.doc.role_profile_name,
				},
				callback: function (data) {
					frm.set_value("roles", []);
					$.each(data.message || [], function (i, v) {
						var d = frm.add_child("roles");
						d.role = v.role;
					});
					frm.roles_editor.show();
				},
			});
		}
	},

	module_profile: function (frm) {
		if (frm.doc.module_profile) {
			dontmanage.call({
				method: "dontmanage.core.doctype.user.user.get_module_profile",
				args: {
					module_profile: frm.doc.module_profile,
				},
				callback: function (data) {
					frm.set_value("block_modules", []);
					$.each(data.message || [], function (i, v) {
						let d = frm.add_child("block_modules");
						d.module = v.module;
					});
					frm.module_editor && frm.module_editor.show();
				},
			});
		}
	},

	onload: function (frm) {
		frm.can_edit_roles = has_access_to_edit_user();

		if (frm.is_new() && frm.roles_editor) {
			frm.roles_editor.reset();
		}

		if (
			frm.can_edit_roles &&
			!frm.is_new() &&
			in_list(["System User", "Website User"], frm.doc.user_type)
		) {
			if (!frm.roles_editor) {
				const role_area = $('<div class="role-editor">').appendTo(
					frm.fields_dict.roles_html.wrapper
				);

				frm.roles_editor = new dontmanage.RoleEditor(
					role_area,
					frm,
					frm.doc.role_profile_name ? 1 : 0
				);

				if (frm.doc.user_type == "System User") {
					var module_area = $("<div>").appendTo(frm.fields_dict.modules_html.wrapper);
					frm.module_editor = new dontmanage.ModuleEditor(frm, module_area);
				}
			} else {
				frm.roles_editor.show();
			}
		}
	},
	refresh: function (frm) {
		let doc = frm.doc;

		if (frm.is_new()) {
			frm.set_value("time_zone", dontmanage.sys_defaults.time_zone);
		}

		if (
			in_list(["System User", "Website User"], frm.doc.user_type) &&
			!frm.is_new() &&
			!frm.roles_editor &&
			frm.can_edit_roles
		) {
			frm.reload_doc();
			return;
		}

		if (
			doc.name === dontmanage.session.user &&
			!doc.__unsaved &&
			dontmanage.all_timezones &&
			(doc.language || dontmanage.boot.user.language) &&
			doc.language !== dontmanage.boot.user.language
		) {
			dontmanage.msgprint(__("Refreshing..."));
			window.location.reload();
		}

		frm.toggle_display(["sb1", "sb3", "modules_access"], false);

		if (!frm.is_new()) {
			if (has_access_to_edit_user()) {
				frm.add_custom_button(
					__("Set User Permissions"),
					function () {
						dontmanage.route_options = {
							user: doc.name,
						};
						dontmanage.set_route("List", "User Permission");
					},
					__("Permissions")
				);

				frm.add_custom_button(
					__("View Permitted Documents"),
					() =>
						dontmanage.set_route("query-report", "Permitted Documents For User", {
							user: frm.doc.name,
						}),
					__("Permissions")
				);

				frm.toggle_display(["sb1", "sb3", "modules_access"], true);
			}

			frm.add_custom_button(
				__("Reset Password"),
				function () {
					dontmanage.call({
						method: "dontmanage.core.doctype.user.user.reset_password",
						args: {
							user: frm.doc.name,
						},
					});
				},
				__("Password")
			);

			if (dontmanage.user.has_role("System Manager")) {
				dontmanage.db.get_single_value("LDAP Settings", "enabled").then((value) => {
					if (value === 1 && frm.doc.name != "Administrator") {
						frm.add_custom_button(
							__("Reset LDAP Password"),
							function () {
								const d = new dontmanage.ui.Dialog({
									title: __("Reset LDAP Password"),
									fields: [
										{
											label: __("New Password"),
											fieldtype: "Password",
											fieldname: "new_password",
											reqd: 1,
										},
										{
											label: __("Confirm New Password"),
											fieldtype: "Password",
											fieldname: "confirm_password",
											reqd: 1,
										},
										{
											label: __("Logout All Sessions"),
											fieldtype: "Check",
											fieldname: "logout_sessions",
										},
									],
									primary_action: (values) => {
										d.hide();
										if (values.new_password !== values.confirm_password) {
											dontmanage.throw(__("Passwords do not match!"));
										}
										dontmanage.call(
											"dontmanage.integrations.doctype.ldap_settings.ldap_settings.reset_password",
											{
												user: frm.doc.email,
												password: values.new_password,
												logout: values.logout_sessions,
											}
										);
									},
								});
								d.show();
							},
							__("Password")
						);
					}
				});
			}

			if (dontmanage.session.user == doc.name || dontmanage.user.has_role("System Manager")) {
				frm.add_custom_button(
					__("Reset OTP Secret"),
					function () {
						dontmanage.call({
							method: "dontmanage.twofactor.reset_otp_secret",
							args: {
								user: frm.doc.name,
							},
						});
					},
					__("Password")
				);
			}

			frm.trigger("enabled");

			if (frm.roles_editor && frm.can_edit_roles) {
				frm.roles_editor.disable = frm.doc.role_profile_name ? 1 : 0;
				frm.roles_editor.show();
			}

			frm.module_editor && frm.module_editor.show();

			if (dontmanage.session.user == doc.name) {
				// update display settings
				if (doc.user_image) {
					dontmanage.boot.user_info[dontmanage.session.user].image = dontmanage.utils.get_file_link(
						doc.user_image
					);
				}
			}
		}
		if (frm.doc.user_emails && dontmanage.model.can_create("Email Account")) {
			var found = 0;
			for (var i = 0; i < frm.doc.user_emails.length; i++) {
				if (frm.doc.email == frm.doc.user_emails[i].email_id) {
					found = 1;
				}
			}
			if (!found) {
				frm.add_custom_button(__("Create User Email"), function () {
					frm.events.create_user_email(frm);
				});
			}
		}

		if (dontmanage.route_flags.unsaved === 1) {
			delete dontmanage.route_flags.unsaved;
			for (var i = 0; i < frm.doc.user_emails.length; i++) {
				frm.doc.user_emails[i].idx = frm.doc.user_emails[i].idx + 1;
			}
			frm.dirty();
		}
		frm.trigger("time_zone");
	},
	validate: function (frm) {
		if (frm.roles_editor) {
			frm.roles_editor.set_roles_in_table();
		}
	},
	enabled: function (frm) {
		var doc = frm.doc;
		if (!frm.is_new() && has_access_to_edit_user()) {
			frm.toggle_display(["sb1", "sb3", "modules_access"], doc.enabled);
			frm.set_df_property("enabled", "read_only", 0);
		}

		if (dontmanage.session.user !== "Administrator") {
			frm.toggle_enable("email", frm.is_new());
		}
	},
	create_user_email: function (frm) {
		dontmanage.call({
			method: "dontmanage.core.doctype.user.user.has_email_account",
			args: {
				email: frm.doc.email,
			},
			callback: function (r) {
				if (!Array.isArray(r.message)) {
					dontmanage.route_options = {
						email_id: frm.doc.email,
						awaiting_password: 1,
						enable_incoming: 1,
					};
					dontmanage.model.with_doctype("Email Account", function (doc) {
						var doc = dontmanage.model.get_new_doc("Email Account");
						dontmanage.route_flags.linked_user = frm.doc.name;
						dontmanage.route_flags.delete_user_from_locals = true;
						dontmanage.set_route("Form", "Email Account", doc.name);
					});
				} else {
					dontmanage.route_flags.create_user_account = frm.doc.name;
					dontmanage.set_route("Form", "Email Account", r.message[0]["name"]);
				}
			},
		});
	},
	generate_keys: function (frm) {
		dontmanage.call({
			method: "dontmanage.core.doctype.user.user.generate_keys",
			args: {
				user: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					dontmanage.msgprint(__("Save API Secret: {0}", [r.message.api_secret]));
					frm.reload_doc();
				}
			},
		});
	},
	on_update: function (frm) {
		if (dontmanage.boot.time_zone && dontmanage.boot.time_zone.user !== frm.doc.time_zone) {
			// Clear cache after saving to refresh the values of boot.
			dontmanage.ui.toolbar.clear_cache();
		}
	},
});

dontmanage.ui.form.on("User Email", {
	email_account(frm, cdt, cdn) {
		let child_row = locals[cdt][cdn];
		dontmanage.model.get_value(
			"Email Account",
			child_row.email_account,
			"auth_method",
			(value) => {
				child_row.used_oauth = value.auth_method === "OAuth";
				frm.refresh_field("user_emails", cdn, "used_oauth");
			}
		);
	},
});

function has_access_to_edit_user() {
	return has_common(dontmanage.user_roles, get_roles_for_editing_user());
}

function get_roles_for_editing_user() {
	return (
		dontmanage
			.get_meta("User")
			.permissions.filter((perm) => perm.permlevel >= 1 && perm.write)
			.map((perm) => perm.role) || ["System Manager"]
	);
}

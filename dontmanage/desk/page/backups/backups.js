dontmanage.pages["backups"].on_page_load = function (wrapper) {
	var page = dontmanage.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		dontmanage.set_route("Form", "System Settings");
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		dontmanage.call({
			method: "dontmanage.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: dontmanage.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		if (dontmanage.user.has_role("System Manager")) {
			dontmanage.verify_password(function () {
				dontmanage.call({
					method: "dontmanage.utils.backups.get_backup_encryption_key",
					callback: function (r) {
						dontmanage.msgprint({
							title: __("Backup Encryption Key"),
							message: __(r.message),
							indicator: "blue",
						});
					},
				});
			});
		} else {
			dontmanage.msgprint({
				title: __("Error"),
				message: __("System Manager privileges required."),
				indicator: "red",
			});
		}
	});

	dontmanage.breadcrumbs.add("Setup");

	$(dontmanage.render_template("backups")).appendTo(page.body.addClass("no-border"));
};

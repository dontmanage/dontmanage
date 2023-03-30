dontmanage.listview_settings["RQ Job"] = {
	hide_name_column: true,

	onload(listview) {
		if (!has_common(dontmanage.user_roles, ["Administrator", "System Manager"])) return;

		listview.page.add_inner_button(
			__("Remove Failed Jobs"),
			() => {
				dontmanage.confirm(__("Are you sure you want to remove all failed jobs?"), () => {
					dontmanage.xcall("dontmanage.core.doctype.rq_job.rq_job.remove_failed_jobs");
				});
			},
			__("Actions")
		);

		if (listview.list_view_settings) {
			listview.list_view_settings.disable_count = 1;
			listview.list_view_settings.disable_sidebar_stats = 1;
		}

		dontmanage.xcall("dontmanage.utils.scheduler.get_scheduler_status").then(({ status }) => {
			if (status === "active") {
				listview.page.set_indicator(__("Scheduler: Active"), "green");
			} else {
				listview.page.set_indicator(__("Scheduler: Inactive"), "red");
				listview.page.add_inner_button(
					__("Enable Scheduler"),
					() => {
						dontmanage.confirm(__("Are you sure you want to re-enable scheduler?"), () => {
							dontmanage
								.xcall("dontmanage.utils.scheduler.activate_scheduler")
								.then(() => {
									dontmanage.show_alert(__("Enabled Scheduler"));
								})
								.catch((e) => {
									dontmanage.show_alert({
										message: __("Failed to enable scheduler: {0}", e),
										indicator: "error",
									});
								});
						});
					},
					__("Actions")
				);
			}
		});

		setInterval(() => {
			if (!listview.list_view_settings.disable_auto_refresh) {
				listview.refresh();
			}
		}, 5000);
	},
};

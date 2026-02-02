dontmanage.listview_settings["Webhook Request Log"] = {
	onload: function (list_view) {
		dontmanage.require("logtypes.bundle.js", () => {
			dontmanage.utils.logtypes.show_log_retention_message(list_view.doctype);
		});
	},
};

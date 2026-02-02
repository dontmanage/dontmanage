dontmanage.listview_settings["Scheduled Job Log"] = {
	onload: function (listview) {
		dontmanage.require("logtypes.bundle.js", () => {
			dontmanage.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};

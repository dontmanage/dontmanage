dontmanage.listview_settings["File"] = {
	formatters: {
		file_name: function (value) {
			return dontmanage.utils.escape_html(value || "");
		},
	},
};

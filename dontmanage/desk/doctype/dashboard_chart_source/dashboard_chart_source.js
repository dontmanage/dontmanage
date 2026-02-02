// Copyright (c) 2019, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Dashboard Chart Source", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Dashboard Chart"),
				function () {
					let dashboard_chart = dontmanage.model.get_new_doc("Dashboard Chart");
					dashboard_chart.chart_type = "Custom";
					dashboard_chart.source = frm.doc.name;
					dontmanage.set_route("Form", "Dashboard Chart", dashboard_chart.name);
				},
				__("Create")
			);
		}
	},
});

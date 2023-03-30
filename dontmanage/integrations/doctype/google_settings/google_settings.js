// Copyright (c) 2019, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Google Settings", {
	refresh: function (frm) {
		frm.dashboard.set_headline(
			__("For more information, {0}.", [
				`<a href='https://dontmanageerp.com/docs/user/manual/en/dontmanageerp_integration/google_settings'>${__(
					"Click here"
				)}</a>`,
			])
		);
	},
});

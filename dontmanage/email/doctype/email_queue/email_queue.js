// Copyright (c) 2016, DontManage Technologies and contributors
// For license information, please see license.txt

dontmanage.ui.form.on("Email Queue", {
	refresh: function (frm) {
		if (["Not Sent", "Partially Sent"].includes(frm.doc.status)) {
			let button = frm.add_custom_button("Send Now", function () {
				dontmanage.call({
					method: "dontmanage.email.doctype.email_queue.email_queue.send_now",
					args: {
						name: frm.doc.name,
						force_send: true,
					},
					btn: button,
					callback: function () {
						frm.reload_doc();
						if (cint(dontmanage.sys_defaults.suspend_email_queue)) {
							dontmanage.show_alert(
								__(
									"Email queue is currently suspended. Resume to automatically send other emails."
								)
							);
						}
					},
				});
			});
		} else if (frm.doc.status == "Error") {
			frm.add_custom_button("Retry Sending", function () {
				frm.call({
					method: "dontmanage.email.doctype.email_queue.email_queue.retry_sending",
					args: {
						queues: [frm.doc.name],
					},
					callback: function () {
						frm.reload_doc();
						dontmanage.show_alert({
							message: __(
								"Status Updated. The email will be picked up in the next scheduled run."
							),
							indicator: "green",
						});
					},
				});
			});
		}

		if (frm.doc.__onload?.mute_emails) {
			frm.dashboard.set_headline(
				__("Automatic sending of emails is disabled via site config.")
			);
		}
	},
});

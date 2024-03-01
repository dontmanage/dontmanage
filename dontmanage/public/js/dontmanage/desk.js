// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

dontmanage.start_app = function () {
	if (!dontmanage.Application) return;
	dontmanage.assets.check();
	dontmanage.provide("dontmanage.app");
	dontmanage.provide("dontmanage.desk");
	dontmanage.app = new dontmanage.Application();
};

$(document).ready(function () {
	if (!dontmanage.utils.supportsES6) {
		dontmanage.msgprint({
			indicator: "red",
			title: __("Browser not supported"),
			message: __(
				"Some of the features might not work in your browser. Please update your browser to the latest version."
			),
		});
	}
	dontmanage.start_app();
});

dontmanage.Application = class Application {
	constructor() {
		this.startup();
	}

	startup() {
		dontmanage.realtime.init();
		dontmanage.model.init();

		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.set_favicon();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();

		dontmanage.ui.keys.setup();

		dontmanage.ui.keys.add_shortcut({
			shortcut: "shift+ctrl+g",
			description: __("Switch Theme"),
			action: () => {
				if (dontmanage.theme_switcher && dontmanage.theme_switcher.dialog.is_visible) {
					dontmanage.theme_switcher.hide();
				} else {
					dontmanage.theme_switcher = new dontmanage.ui.ThemeSwitcher();
					dontmanage.theme_switcher.show();
				}
			},
		});

		dontmanage.ui.add_system_theme_switch_listener();
		const root = document.documentElement;

		const observer = new MutationObserver(() => {
			dontmanage.ui.set_theme();
		});
		observer.observe(root, {
			attributes: true,
			attributeFilter: ["data-theme-mode"],
		});

		dontmanage.ui.set_theme();

		// page container
		this.make_page_container();
		if (
			!window.Cypress &&
			dontmanage.boot.onboarding_tours &&
			dontmanage.boot.user.onboarding_status != null
		) {
			let pending_tours = !dontmanage.boot.onboarding_tours.every(
				(tour) => dontmanage.boot.user.onboarding_status[tour[0]]?.is_complete
			);
			if (pending_tours && dontmanage.boot.onboarding_tours.length > 0) {
				dontmanage.require("onboarding_tours.bundle.js", () => {
					dontmanage.utils.sleep(1000).then(() => {
						dontmanage.ui.init_onboarding_tour();
					});
				});
			}
		}
		this.set_route();

		// trigger app startup
		$(document).trigger("startup");

		$(document).trigger("app_ready");

		if (dontmanage.boot.messages) {
			dontmanage.msgprint(dontmanage.boot.messages);
		}

		if (dontmanage.user_roles.includes("System Manager")) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!dontmanage.boot.developer_mode) {
			let console_security_message = __(
				"Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand."
			);
			console.log(`%c${console_security_message}`, "font-size: large");
		}

		this.show_notes();

		if (dontmanage.ui.startup_setup_dialog && !dontmanage.boot.setup_complete) {
			dontmanage.ui.startup_setup_dialog.pre_show();
			dontmanage.ui.startup_setup_dialog.show();
		}

		dontmanage.realtime.on("version-update", function () {
			var dialog = dontmanage.msgprint({
				message: __(
					"The application has been updated to a new version, please refresh this page"
				),
				indicator: "green",
				title: __("Version Updated"),
			});
			dialog.set_primary_action(__("Refresh"), function () {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});

		// listen to build errors
		this.setup_build_events();

		if (dontmanage.sys_defaults.email_user_password) {
			var email_list = dontmanage.sys_defaults.email_user_password.split(",");
			for (var u in email_list) {
				if (email_list[u] === dontmanage.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new dontmanage.ui.LinkPreview();
	}

	set_route() {
		if (dontmanage.boot && localStorage.getItem("session_last_route")) {
			dontmanage.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			dontmanage.router.route();
		}
		dontmanage.router.on("change", () => {
			$(".tooltip").hide();
		});
	}

	set_password(user) {
		var me = this;
		dontmanage.call({
			method: "dontmanage.core.doctype.user.user.get_email_awaiting",
			args: {
				user: user,
			},
			callback: function (email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt(email_account, user, i);
					}
				}
			},
		});
	}

	email_password_prompt(email_account, user, i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new dontmanage.ui.Dialog({
			title: __("Password missing in Email Account"),
			fields: [
				{
					fieldname: "password",
					fieldtype: "Password",
					label: __(
						"Please enter the password for: <b>{0}</b>",
						[email_id],
						"Email Account"
					),
					reqd: 1,
				},
				{
					fieldname: "submit",
					fieldtype: "Button",
					label: __("Submit", null, "Submit password for Email Account"),
				},
			],
		});
		d.get_input("submit").on("click", function () {
			//setup spinner
			d.hide();
			var s = new dontmanage.ui.Dialog({
				title: __("Checking one moment"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "checking",
					},
				],
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			dontmanage.call({
				method: "dontmanage.email.doctype.email_account.email_account.set_email_password",
				args: {
					email_account: email_account[i]["email_account"],
					password: d.get_value("password"),
				},
				callback: function (passed) {
					s.hide();
					d.hide(); //hide waiting indication
					if (!passed["message"]) {
						dontmanage.show_alert(
							{ message: __("Login Failed please try again"), indicator: "error" },
							5
						);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}
				},
			});
		});
		d.show();
	}
	load_bootinfo() {
		if (dontmanage.boot) {
			this.setup_workspaces();
			dontmanage.model.sync(dontmanage.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			dontmanage.router.setup();
			this.setup_moment();
			if (dontmanage.boot.print_css) {
				dontmanage.dom.set_style(dontmanage.boot.print_css, "print-style");
			}
			dontmanage.user.name = dontmanage.boot.user.name;
			dontmanage.router.setup();
		} else {
			this.set_as_guest();
		}
	}

	setup_workspaces() {
		dontmanage.modules = {};
		dontmanage.workspaces = {};
		for (let page of dontmanage.boot.allowed_workspaces || []) {
			dontmanage.modules[page.module] = page;
			dontmanage.workspaces[dontmanage.router.slug(page.name)] = page;
		}
	}

	load_user_permissions() {
		dontmanage.defaults.load_user_permission_from_boot();

		dontmanage.realtime.on(
			"update_user_permissions",
			dontmanage.utils.debounce(() => {
				dontmanage.defaults.update_user_permissions();
			}, 500)
		);
	}

	check_metadata_cache_status() {
		if (dontmanage.boot.metadata_version != localStorage.metadata_version) {
			dontmanage.assets.clear_local_storage();
			dontmanage.assets.init_local_storage();
		}
	}

	set_globals() {
		dontmanage.session.user = dontmanage.boot.user.name;
		dontmanage.session.logged_in_user = dontmanage.boot.user.name;
		dontmanage.session.user_email = dontmanage.boot.user.email;
		dontmanage.session.user_fullname = dontmanage.user_info().fullname;

		dontmanage.user_defaults = dontmanage.boot.user.defaults;
		dontmanage.user_roles = dontmanage.boot.user.roles;
		dontmanage.sys_defaults = dontmanage.boot.sysdefaults;

		dontmanage.ui.py_date_format = dontmanage.boot.sysdefaults.date_format
			.replace("dd", "%d")
			.replace("mm", "%m")
			.replace("yyyy", "%Y");
		dontmanage.boot.user.last_selected_values = {};
	}
	sync_pages() {
		// clear cached pages if timestamp is not found
		if (localStorage["page_info"]) {
			dontmanage.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(dontmanage.boot.page_info, function (name, p) {
				if (!page_info[name] || page_info[name].modified != p.modified) {
					delete localStorage["_page:" + name];
				}
				dontmanage.boot.allowed_pages.push(name);
			});
		} else {
			dontmanage.boot.allowed_pages = Object.keys(dontmanage.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(dontmanage.boot.page_info);
	}
	set_as_guest() {
		dontmanage.session.user = "Guest";
		dontmanage.session.user_email = "";
		dontmanage.session.user_fullname = "Guest";

		dontmanage.user_defaults = {};
		dontmanage.user_roles = ["Guest"];
		dontmanage.sys_defaults = {};
	}
	make_page_container() {
		if ($("#body").length) {
			$(".splash").remove();
			dontmanage.temp_container = $("<div id='temp-container' style='display: none;'>").appendTo(
				"body"
			);
			dontmanage.container = new dontmanage.views.Container();
		}
	}
	make_nav_bar() {
		// toolbar
		if (dontmanage.boot && dontmanage.boot.home_page !== "setup-wizard") {
			dontmanage.dontmanage_toolbar = new dontmanage.ui.toolbar.Toolbar();
		}
	}
	logout() {
		var me = this;
		me.logged_out = true;
		return dontmanage.call({
			method: "logout",
			callback: function (r) {
				if (r.exc) {
					return;
				}
				me.redirect_to_login();
			},
		});
	}
	handle_session_expired() {
		dontmanage.app.redirect_to_login();
	}
	redirect_to_login() {
		window.location.href = `/login?redirect-to=${encodeURIComponent(
			window.location.pathname + window.location.search
		)}`;
	}
	set_favicon() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	}
	trigger_primary_action() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(":visible")) {
				cur_frm.page.btn_primary.trigger("click");
			} else if (dontmanage.container.page.save_action) {
				dontmanage.container.page.save_action();
			}
		}, 100);
	}

	show_change_log() {
		var me = this;
		let change_log = dontmanage.boot.change_log;

		// dontmanage.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "DontManageErp",
		// 	"version": "12.2.0"
		// }];

		if (
			!Array.isArray(change_log) ||
			!change_log.length ||
			window.Cypress ||
			cint(dontmanage.boot.sysdefaults.disable_change_log_notification)
		) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = dontmanage.msgprint({
			message: dontmanage.render_template("change_log", { change_log: change_log }),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function () {
			dontmanage.call({
				method: "dontmanage.utils.change_log.update_last_known_versions",
			});
			me.show_notes();
		};
	}

	show_update_available() {
		if (dontmanage.boot.sysdefaults.disable_system_update_notification) return;

		dontmanage.call({
			method: "dontmanage.utils.change_log.show_update_popup",
		});
	}

	add_browser_class() {
		$("html").addClass(dontmanage.utils.get_browser().name.toLowerCase());
	}

	set_fullwidth_if_enabled() {
		dontmanage.ui.toolbar.set_fullwidth_if_enabled();
	}

	show_notes() {
		var me = this;
		if (dontmanage.boot.notes.length) {
			dontmanage.boot.notes.forEach(function (note) {
				if (!note.seen || note.notify_on_every_login) {
					var d = dontmanage.msgprint({ message: note.content, title: note.title });
					d.keep_open = true;
					d.custom_onhide = function () {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							dontmanage.call({
								method: "dontmanage.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name,
								},
							});
						}

						// next note
						me.show_notes();
					};
				}
			});
		}
	}

	setup_build_events() {
		if (dontmanage.boot.developer_mode) {
			dontmanage.require("build_events.bundle.js");
		}
	}

	setup_energy_point_listeners() {
		dontmanage.realtime.on("energy_point_alert", (message) => {
			dontmanage.show_alert(message);
		});
	}

	setup_copy_doc_listener() {
		$("body").on("paste", (e) => {
			try {
				let pasted_data = dontmanage.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					const sleep = dontmanage.utils.sleep;

					dontmanage.dom.freeze(__("Creating {0}", [doc.doctype]) + "...");
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = dontmanage.model.with_doctype(doc.doctype, () => {
							let newdoc = dontmanage.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							dontmanage.set_route("Form", newdoc.doctype, newdoc.name);
							dontmanage.dom.unfreeze();
						});
						res && res.fail(dontmanage.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	}

	setup_moment() {
		moment.updateLocale("en", {
			week: {
				dow: dontmanage.datetime.get_first_day_of_the_week_index(),
			},
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (dontmanage.boot.timezone_info) {
			moment.tz.add(dontmanage.boot.timezone_info);
		}
	}
};

dontmanage.get_module = function (m, default_module) {
	var module = dontmanage.modules[m] || default_module;
	if (!module) {
		return;
	}

	if (module._setup) {
		return module;
	}

	if (!module.label) {
		module.label = m;
	}

	if (!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};

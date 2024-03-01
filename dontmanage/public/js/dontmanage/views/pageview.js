// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.provide("dontmanage.views.pageview");
dontmanage.provide("dontmanage.standard_pages");

dontmanage.views.pageview = {
	with_page: function (name, callback) {
		if (dontmanage.standard_pages[name]) {
			if (!dontmanage.pages[name]) {
				dontmanage.standard_pages[name]();
			}
			callback();
			return;
		}

		if (
			(locals.Page && locals.Page[name] && locals.Page[name].script) ||
			name == window.page_name
		) {
			// already loaded
			callback();
		} else if (localStorage["_page:" + name] && dontmanage.boot.developer_mode != 1) {
			// cached in local storage
			dontmanage.model.sync(JSON.parse(localStorage["_page:" + name]));
			callback();
		} else if (name) {
			// get fresh
			return dontmanage.call({
				method: "dontmanage.desk.desk_page.getpage",
				args: { name: name },
				callback: function (r) {
					if (!r.docs._dynamic_page) {
						try {
							localStorage["_page:" + name] = JSON.stringify(r.docs);
						} catch (e) {
							console.warn(e);
						}
					}
					callback();
				},
				freeze: true,
			});
		}
	},

	show: function (name) {
		if (!name) {
			name = dontmanage.boot ? dontmanage.boot.home_page : window.page_name;
		}
		dontmanage.model.with_doctype("Page", function () {
			dontmanage.views.pageview.with_page(name, function (r) {
				if (r && r.exc) {
					if (!r["403"]) dontmanage.show_not_found(name);
				} else if (!dontmanage.pages[name]) {
					new dontmanage.views.Page(name);
				}
				dontmanage.container.change_to(name);
			});
		});
	},
};

dontmanage.views.Page = class Page {
	constructor(name) {
		this.name = name;
		var me = this;

		// web home page
		if (name == window.page_name) {
			this.wrapper = document.getElementById("page-" + name);
			this.wrapper.label = document.title || window.page_name;
			this.wrapper.page_name = window.page_name;
			dontmanage.pages[window.page_name] = this.wrapper;
		} else {
			this.pagedoc = locals.Page[this.name];
			if (!this.pagedoc) {
				dontmanage.show_not_found(name);
				return;
			}
			this.wrapper = dontmanage.container.add_page(this.name);
			this.wrapper.page_name = this.pagedoc.name;

			// set content, script and style
			if (this.pagedoc.content) this.wrapper.innerHTML = this.pagedoc.content;
			dontmanage.dom.eval(this.pagedoc.__script || this.pagedoc.script || "");
			dontmanage.dom.set_style(this.pagedoc.style || "");

			// set breadcrumbs
			dontmanage.breadcrumbs.add(this.pagedoc.module || null);
		}

		this.trigger_page_event("on_page_load");

		// set events
		$(this.wrapper).on("show", function () {
			window.cur_frm = null;
			me.trigger_page_event("on_page_show");
			me.trigger_page_event("refresh");
		});
	}

	trigger_page_event(eventname) {
		var me = this;
		if (me.wrapper[eventname]) {
			me.wrapper[eventname](me.wrapper);
		}
	}
};

dontmanage.show_not_found = function (page_name) {
	dontmanage.show_message_page({
		page_name: page_name,
		message: __("Sorry! I could not find what you were looking for."),
		img: "/assets/dontmanage/images/ui/bubble-tea-sorry.svg",
	});
};

dontmanage.show_not_permitted = function (page_name) {
	dontmanage.show_message_page({
		page_name: page_name,
		message: __("Sorry! You are not permitted to view this page."),
		img: "/assets/dontmanage/images/ui/bubble-tea-sorry.svg",
		// icon: "octicon octicon-circle-slash"
	});
};

dontmanage.show_message_page = function (opts) {
	// opts can include `page_name`, `message`, `icon` or `img`
	if (!opts.page_name) {
		opts.page_name = dontmanage.get_route_str();
	}

	if (opts.icon) {
		opts.img = repl('<span class="%(icon)s message-page-icon"></span> ', opts);
	} else if (opts.img) {
		opts.img = repl('<img src="%(img)s" class="message-page-image">', opts);
	}

	var page = dontmanage.pages[opts.page_name] || dontmanage.container.add_page(opts.page_name);
	$(page).html(
		repl(
			'<div class="page message-page">\
			<div class="text-center message-page-content">\
				%(img)s\
				<p class="lead">%(message)s</p>\
				<a class="btn btn-default btn-sm btn-home" href="/app">%(home)s</a>\
			</div>\
		</div>',
			{
				img: opts.img || "",
				message: opts.message || "",
				home: __("Home"),
			}
		)
	);

	dontmanage.container.change_to(opts.page_name);
};

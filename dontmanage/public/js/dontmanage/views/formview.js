// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.provide("dontmanage.views.formview");

dontmanage.views.FormFactory = class FormFactory extends dontmanage.views.Factory {
	make(route) {
		var doctype = route[1],
			doctype_layout = dontmanage.router.doctype_layout || doctype;

		if (!dontmanage.views.formview[doctype_layout]) {
			dontmanage.model.with_doctype(doctype, () => {
				this.page = dontmanage.container.add_page(doctype_layout);
				dontmanage.views.formview[doctype_layout] = this.page;
				this.make_and_show(doctype, route);
			});
		} else {
			this.show_doc(route);
		}

		this.setup_events();
	}

	make_and_show(doctype, route) {
		if (dontmanage.router.doctype_layout) {
			dontmanage.model.with_doc("DocType Layout", dontmanage.router.doctype_layout, () => {
				this.make_form(doctype);
				this.show_doc(route);
			});
		} else {
			this.make_form(doctype);
			this.show_doc(route);
		}
	}

	make_form(doctype) {
		this.page.frm = new dontmanage.ui.form.Form(
			doctype,
			this.page,
			true,
			dontmanage.router.doctype_layout
		);
	}

	setup_events() {
		if (!this.initialized) {
			$(document).on("page-change", function () {
				dontmanage.ui.form.close_grid_form();
			});

			dontmanage.realtime.on("doc_viewers", function (data) {
				// set users that currently viewing the form
				dontmanage.ui.form.FormViewers.set_users(data, "viewers");
			});

			dontmanage.realtime.on("doc_typers", function (data) {
				// set users that currently typing on the form
				dontmanage.ui.form.FormViewers.set_users(data, "typers");
			});
		}
		this.initialized = true;
	}

	show_doc(route) {
		var doctype = route[1],
			doctype_layout = dontmanage.router.doctype_layout || doctype,
			name = route.slice(2).join("/");

		if (dontmanage.model.new_names[name]) {
			// document has been renamed, reroute
			name = dontmanage.model.new_names[name];
			dontmanage.set_route("Form", doctype_layout, name);
			return;
		}

		const doc = dontmanage.get_doc(doctype, name);
		if (
			doc &&
			dontmanage.model.get_docinfo(doctype, name) &&
			(doc.__islocal || dontmanage.model.is_fresh(doc))
		) {
			// is document available and recent?
			this.render(doctype_layout, name);
		} else {
			this.fetch_and_render(doctype, name, doctype_layout);
		}
	}

	fetch_and_render(doctype, name, doctype_layout) {
		dontmanage.model.with_doc(doctype, name, (name, r) => {
			if (r && r["403"]) return; // not permitted

			if (!(locals[doctype] && locals[doctype][name])) {
				if (name && name.substr(0, 3) === "new") {
					this.render_new_doc(doctype, name, doctype_layout);
				} else {
					dontmanage.show_not_found();
				}
				return;
			}
			this.render(doctype_layout, name);
		});
	}

	render_new_doc(doctype, name, doctype_layout) {
		const new_name = dontmanage.model.make_new_doc_and_get_name(doctype, true);
		if (new_name === name) {
			this.render(doctype_layout, name);
		} else {
			dontmanage.route_flags.replace_route = true;
			dontmanage.set_route("Form", doctype_layout, new_name);
		}
	}

	render(doctype_layout, name) {
		dontmanage.container.change_to(doctype_layout);
		dontmanage.views.formview[doctype_layout].frm.refresh(name);
	}
};

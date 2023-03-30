// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

dontmanage.provide("dontmanage.pages");
dontmanage.provide("dontmanage.views");

dontmanage.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		this.route = dontmanage.get_route();
		this.page_name = dontmanage.get_route_str();

		if (this.before_show && this.before_show() === false) return;

		if (dontmanage.pages[this.page_name]) {
			dontmanage.container.change_to(this.page_name);
			if (this.on_show) {
				this.on_show();
			}
		} else {
			if (this.route[1]) {
				this.make(this.route);
			} else {
				dontmanage.show_not_found(this.route);
			}
		}
	}

	make_page(double_column, page_name) {
		return dontmanage.make_page(double_column, page_name);
	}
};

dontmanage.make_page = function (double_column, page_name) {
	if (!page_name) {
		page_name = dontmanage.get_route_str();
	}

	const page = dontmanage.container.add_page(page_name);

	dontmanage.ui.make_app_page({
		parent: page,
		single_column: !double_column,
	});

	dontmanage.container.change_to(page_name);
	return page;
};

// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

// provide a namespace
if (!window.dontmanage) window.dontmanage = {};

dontmanage.provide = function (namespace) {
	// docs: create a namespace //
	var nsl = namespace.split(".");
	var parent = window;
	for (var i = 0; i < nsl.length; i++) {
		var n = nsl[i];
		if (!parent[n]) {
			parent[n] = {};
		}
		parent = parent[n];
	}
	return parent;
};

dontmanage.provide("locals");
dontmanage.provide("dontmanage.flags");
dontmanage.provide("dontmanage.settings");
dontmanage.provide("dontmanage.utils");
dontmanage.provide("dontmanage.ui.form");
dontmanage.provide("dontmanage.modules");
dontmanage.provide("dontmanage.templates");
dontmanage.provide("dontmanage.test_data");
dontmanage.provide("dontmanage.utils");
dontmanage.provide("dontmanage.model");
dontmanage.provide("dontmanage.user");
dontmanage.provide("dontmanage.session");
dontmanage.provide("dontmanage._messages");
dontmanage.provide("locals.DocType");

// for listviews
dontmanage.provide("dontmanage.listview_settings");
dontmanage.provide("dontmanage.tour");
dontmanage.provide("dontmanage.listview_parent_route");

// constants
window.NEWLINE = "\n";
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm = null;

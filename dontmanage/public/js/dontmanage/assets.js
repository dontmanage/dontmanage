// Copyright (c) 2015, DontManage and Contributors
// MIT License. See license.txt

// library to mange assets (js, css, models, html) etc in the app.
// will try and get from localStorage if latest are available
// depends on dontmanage.versions to manage versioning

dontmanage.require = function (items, callback) {
	if (typeof items === "string") {
		items = [items];
	}
	items = items.map((item) => dontmanage.assets.bundled_asset(item));

	return new Promise((resolve) => {
		dontmanage.assets.execute(items, () => {
			resolve();
			callback && callback();
		});
	});
};

dontmanage.assets = {
	check: function () {
		// if version is different then clear localstorage
		if (window._version_number != localStorage.getItem("_version_number")) {
			dontmanage.assets.clear_local_storage();
			console.log("Cleared App Cache.");
		}

		if (localStorage._last_load) {
			var not_updated_since = new Date() - new Date(localStorage._last_load);
			if (not_updated_since < 10000 || not_updated_since > 86400000) {
				dontmanage.assets.clear_local_storage();
			}
		} else {
			dontmanage.assets.clear_local_storage();
		}

		dontmanage.assets.init_local_storage();
	},

	init_local_storage: function () {
		localStorage._last_load = new Date();
		localStorage._version_number = window._version_number;
		if (dontmanage.boot) localStorage.metadata_version = dontmanage.boot.metadata_version;
	},

	clear_local_storage: function () {
		$.each(
			["_last_load", "_version_number", "metadata_version", "page_info", "last_visited"],
			function (i, key) {
				localStorage.removeItem(key);
			}
		);

		// clear assets
		for (var key in localStorage) {
			if (
				key.indexOf("desk_assets:") === 0 ||
				key.indexOf("_page:") === 0 ||
				key.indexOf("_doctype:") === 0 ||
				key.indexOf("preferred_breadcrumbs:") === 0
			) {
				localStorage.removeItem(key);
			}
		}
		console.log("localStorage cleared");
	},

	// keep track of executed assets
	executed_: [],

	// pass on to the handler to set
	execute: function (items, callback) {
		var to_fetch = [];
		for (var i = 0, l = items.length; i < l; i++) {
			if (!dontmanage.assets.exists(items[i])) {
				to_fetch.push(items[i]);
			}
		}
		if (to_fetch.length) {
			dontmanage.assets.fetch(to_fetch, function () {
				dontmanage.assets.eval_assets(items, callback);
			});
		} else {
			dontmanage.assets.eval_assets(items, callback);
		}
	},

	eval_assets: function (items, callback) {
		for (var i = 0, l = items.length; i < l; i++) {
			// execute js/css if not already.
			var path = items[i];
			if (dontmanage.assets.executed_.indexOf(path) === -1) {
				// execute
				dontmanage.assets.handler[dontmanage.assets.extn(path)](dontmanage.assets.get(path), path);
				dontmanage.assets.executed_.push(path);
			}
		}
		callback && callback();
	},

	// check if the asset exists in
	// localstorage
	exists: function (src) {
		if (dontmanage.assets.executed_.indexOf(src) !== -1) {
			return true;
		}
		if (dontmanage.boot.developer_mode) {
			return false;
		}
		if (dontmanage.assets.get(src)) {
			return true;
		} else {
			return false;
		}
	},

	// load an asset via
	fetch: function (items, callback) {
		// this is virtual page load, only get the the source
		// *without* the template

		dontmanage.call({
			type: "GET",
			method: "dontmanage.client.get_js",
			args: {
				items: items,
			},
			callback: function (r) {
				$.each(items, function (i, src) {
					dontmanage.assets.add(src, r.message[i]);
				});
				callback();
			},
			freeze: true,
		});
	},

	add: function (src, txt) {
		if ("localStorage" in window) {
			try {
				dontmanage.assets.set(src, txt);
			} catch (e) {
				// if quota is exceeded, clear local storage and set item
				dontmanage.assets.clear_local_storage();
				dontmanage.assets.set(src, txt);
			}
		}
	},

	get: function (src) {
		return localStorage.getItem("desk_assets:" + src);
	},

	set: function (src, txt) {
		localStorage.setItem("desk_assets:" + src, txt);
	},

	extn: function (src) {
		if (src.indexOf("?") != -1) {
			src = src.split("?").slice(-1)[0];
		}
		return src.split(".").slice(-1)[0];
	},

	handler: {
		js: function (txt, src) {
			dontmanage.dom.eval(txt);
		},
		css: function (txt, src) {
			dontmanage.dom.set_style(txt);
		},
	},

	bundled_asset(path, is_rtl = null) {
		if (!path.startsWith("/assets") && path.includes(".bundle.")) {
			if (path.endsWith(".css") && is_rtl) {
				path = `rtl_${path}`;
			}
			path = dontmanage.boot.assets_json[path] || path;
			return path;
		}
		return path;
	},
};

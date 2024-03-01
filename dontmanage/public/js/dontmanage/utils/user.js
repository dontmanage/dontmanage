dontmanage.user_info = function (uid) {
	if (!uid) uid = dontmanage.session.user;

	let user_info;
	if (!(dontmanage.boot.user_info && dontmanage.boot.user_info[uid])) {
		user_info = { fullname: uid || "Unknown" };
	} else {
		user_info = dontmanage.boot.user_info[uid];
	}

	user_info.abbr = dontmanage.get_abbr(user_info.fullname);
	user_info.color = dontmanage.get_palette(user_info.fullname);

	return user_info;
};

dontmanage.update_user_info = function (user_info) {
	for (let user in user_info) {
		if (dontmanage.boot.user_info[user]) {
			Object.assign(dontmanage.boot.user_info[user], user_info[user]);
		} else {
			dontmanage.boot.user_info[user] = user_info[user];
		}
	}
};

dontmanage.provide("dontmanage.user");

$.extend(dontmanage.user, {
	name: "Guest",
	full_name: function (uid) {
		return uid === dontmanage.session.user
			? __(
					"You",
					null,
					"Name of the current user. For example: You edited this 5 hours ago."
			  )
			: dontmanage.user_info(uid).fullname;
	},
	image: function (uid) {
		return dontmanage.user_info(uid).image;
	},
	abbr: function (uid) {
		return dontmanage.user_info(uid).abbr;
	},
	has_role: function (rl) {
		if (typeof rl == "string") rl = [rl];
		for (var i in rl) {
			if ((dontmanage.boot ? dontmanage.boot.user.roles : ["Guest"]).indexOf(rl[i]) != -1)
				return true;
		}
	},
	get_desktop_items: function () {
		// hide based on permission
		var modules_list = $.map(dontmanage.boot.allowed_modules, function (icon) {
			var m = icon.module_name;
			var type = dontmanage.modules[m] && dontmanage.modules[m].type;

			if (dontmanage.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if (dontmanage.boot.user.allow_modules.indexOf(m) != -1 || dontmanage.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if (dontmanage.boot.allowed_pages.indexOf(dontmanage.modules[m].link) != -1) ret = m;
			} else if (type === "list") {
				if (dontmanage.model.can_read(dontmanage.modules[m]._doctype)) ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if (
					dontmanage.user.has_role("System Manager") ||
					dontmanage.user.has_role("Administrator")
				)
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function () {
		return dontmanage.user.has_role(["Administrator", "System Manager", "Report Manager"]);
	},

	get_formatted_email: function (email) {
		var fullname = dontmanage.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = "";

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl("%(quote)s%(fullname)s%(quote)s <%(email)s>", {
				fullname: fullname,
				email: email,
				quote: quote,
			});
		}
	},

	get_emails: () => {
		return Object.keys(dontmanage.boot.user_info).map((key) => dontmanage.boot.user_info[key].email);
	},

	/* Normally dontmanage.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (dontmanage.user === 'Administrator')
	 *
	 * dontmanage.user will cast to a string
	 * returning dontmanage.user.name
	 */
	toString: function () {
		return this.name;
	},
});

dontmanage.session_alive = true;
$(document).bind("mousemove", function () {
	if (dontmanage.session_alive === false) {
		$(document).trigger("session_alive");
	}
	dontmanage.session_alive = true;
	if (dontmanage.session_alive_timeout) clearTimeout(dontmanage.session_alive_timeout);
	dontmanage.session_alive_timeout = setTimeout("dontmanage.session_alive=false;", 30000);
});

dontmanage.provide("dontmanage.ui.misc");
dontmanage.ui.misc.about = function () {
	if (!dontmanage.ui.misc.about_dialog) {
		var d = new dontmanage.ui.Dialog({ title: __("DontManage Framework") });

		$(d.body).html(
			repl(
				`<div>
					<p>${__("Open Source Applications for the Web")}</p>
					<p><i class='fa fa-globe fa-fw'></i>
						${__("Website")}:
						<a href='https://dontmanageframework.com' target='_blank'>https://dontmanageframework.com</a></p>
					<p><i class='fa fa-github fa-fw'></i>
						${__("Source")}:
						<a href='https://github.com/dontmanage' target='_blank'>https://github.com/dontmanage</a></p>
					<p><i class='fa fa-graduation-cap fa-fw'></i>
						DontManage School: <a href='https://dontmanage.school' target='_blank'>https://dontmanage.school</a></p>
					<p><i class='fa fa-linkedin fa-fw'></i>
						Linkedin: <a href='https://linkedin.com/company/dontmanage-tech' target='_blank'>https://linkedin.com/company/dontmanage-tech</a></p>
					<p><i class='fa fa-twitter fa-fw'></i>
						Twitter: <a href='https://twitter.com/dontmanagetech' target='_blank'>https://twitter.com/dontmanagetech</a></p>
					<p><i class='fa fa-youtube fa-fw'></i>
						YouTube: <a href='https://www.youtube.com/@dontmanagetech' target='_blank'>https://www.youtube.com/@dontmanagetech</a></p>
					<hr>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<hr>
					<p class='text-muted'>${__("&copy; DontManage and contributors")} </p>
					</div>`,
				dontmanage.app
			)
		);

		dontmanage.ui.misc.about_dialog = d;

		dontmanage.ui.misc.about_dialog.on_page_show = function () {
			if (!dontmanage.versions) {
				dontmanage.call({
					method: "dontmanage.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(dontmanage.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				let text;
				if (v.branch) {
					text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			dontmanage.versions = versions;
		};
	}

	dontmanage.ui.misc.about_dialog.show();
};

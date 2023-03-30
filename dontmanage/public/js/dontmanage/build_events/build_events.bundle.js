import BuildError from "./BuildError.vue";
import BuildSuccess from "./BuildSuccess.vue";

let $container = $("#build-events-overlay");
let success = null;
let error = null;

dontmanage.realtime.on("build_event", (data) => {
	if (data.success) {
		// remove executed cache for rebuilt files
		let changed_files = data.changed_files;
		if (Array.isArray(changed_files)) {
			for (let file of changed_files) {
				if (file.includes(".bundle.")) {
					let parts = file.split(".bundle.");
					if (parts.length === 2) {
						let filename = parts[0].split("/").slice(-1)[0];

						dontmanage.assets.executed_ = dontmanage.assets.executed_.filter(
							(asset) => !asset.includes(`${filename}.bundle`)
						);
					}
				}
			}
		}
		// update assets json
		dontmanage.call("dontmanage.sessions.get_boot_assets_json").then((r) => {
			if (r.message) {
				dontmanage.boot.assets_json = r.message;

				if (dontmanage.hot_update) {
					dontmanage.hot_update.forEach((callback) => {
						callback();
					});
				}
			}
		});
		show_build_success(data);
	} else if (data.error) {
		show_build_error(data);
	}
});

function show_build_success(data) {
	if (error) {
		error.hide();
	}

	if (!success) {
		let target = $('<div class="build-success-container">').appendTo($container).get(0);
		let vm = new Vue({
			el: target,
			render: (h) => h(BuildSuccess),
		});
		success = vm.$children[0];
	}
	success.show(data);
}

function show_build_error(data) {
	if (success) {
		success.hide();
	}
	if (!error) {
		let target = $('<div class="build-error-container">').appendTo($container).get(0);
		let vm = new Vue({
			el: target,
			render: (h) => h(BuildError),
		});
		error = vm.$children[0];
	}
	error.show(data);
}

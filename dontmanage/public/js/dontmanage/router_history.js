dontmanage.route_history_queue = [];
const routes_to_skip = ["Form", "social", "setup-wizard", "recorder"];

const save_routes = dontmanage.utils.debounce(() => {
	if (dontmanage.session.user === "Guest") return;
	const routes = dontmanage.route_history_queue;
	if (!routes.length) return;

	dontmanage.route_history_queue = [];

	dontmanage
		.xcall("dontmanage.desk.doctype.route_history.route_history.deferred_insert", {
			routes: routes,
		})
		.catch(() => {
			dontmanage.route_history_queue.concat(routes);
		});
}, 10000);

dontmanage.router.on("change", () => {
	const route = dontmanage.get_route();
	if (is_route_useful(route)) {
		dontmanage.route_history_queue.push({
			creation: dontmanage.datetime.now_datetime(),
			route: dontmanage.get_route_str(),
		});

		save_routes();
	}
});

function is_route_useful(route) {
	if (!route[1]) {
		return false;
	} else if ((route[0] === "List" && !route[2]) || routes_to_skip.includes(route[0])) {
		return false;
	} else {
		return true;
	}
}

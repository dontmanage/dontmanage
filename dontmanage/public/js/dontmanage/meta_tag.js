dontmanage.provide("dontmanage.model");
dontmanage.provide("dontmanage.utils");

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
dontmanage.utils.set_meta_tag = function (route) {
	dontmanage.db.exists("Website Route Meta", route).then((exists) => {
		if (exists) {
			dontmanage.set_route("Form", "Website Route Meta", route);
		} else {
			// new doc
			const doc = dontmanage.model.get_new_doc("Website Route Meta");
			doc.__newname = route;
			dontmanage.set_route("Form", doc.doctype, doc.name);
		}
	});
};

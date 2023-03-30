import dontmanage

base_template_path = "www/robots.txt"


def get_context(context):
	robots_txt = (
		dontmanage.db.get_single_value("Website Settings", "robots_txt")
		or (dontmanage.local.conf.robots_txt and dontmanage.read_file(dontmanage.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}

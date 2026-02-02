import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "domain")
	dontmanage.reload_doc("core", "doctype", "has_domain")
	active_domains = dontmanage.get_active_domains()
	all_domains = dontmanage.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = dontmanage.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()

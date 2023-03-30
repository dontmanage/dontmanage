import dontmanage


def execute():
	dontmanage.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = dontmanage.utils.get_site_url(dontmanage.local.site)
	dontmanage.db.sql(f"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{site_url}%'""")

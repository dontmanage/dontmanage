import dontmanage


def execute():
	dontmanage.reload_doc("website", "doctype", "web_page_view", force=True)
	dontmanage.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")

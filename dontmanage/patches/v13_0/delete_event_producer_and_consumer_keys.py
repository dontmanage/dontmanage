# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	if dontmanage.db.exists("DocType", "Event Producer"):
		dontmanage.db.sql("""UPDATE `tabEvent Producer` SET api_key='', api_secret=''""")
	if dontmanage.db.exists("DocType", "Event Consumer"):
		dontmanage.db.sql("""UPDATE `tabEvent Consumer` SET api_key='', api_secret=''""")

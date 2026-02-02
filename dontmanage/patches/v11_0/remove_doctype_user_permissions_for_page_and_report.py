# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.delete_doc_if_exists("DocType", "User Permission for Page and Report")

# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	dontmanage.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	dontmanage.delete_doc("DocType", "Package Publish Target", ignore_missing=True)

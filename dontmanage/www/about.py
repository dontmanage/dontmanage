# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage

sitemap = 1


def get_context(context):
	context.doc = dontmanage.get_cached_doc("About Us Settings")

	return context

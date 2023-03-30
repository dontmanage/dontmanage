# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.search.full_text_search import FullTextSearch
from dontmanage.search.website_search import WebsiteSearch
from dontmanage.utils import cint


@dontmanage.whitelist(allow_guest=True)
def web_search(query, scope=None, limit=20):
	limit = cint(limit)
	ws = WebsiteSearch(index_name="web_routes")
	return ws.search(query, scope, limit)

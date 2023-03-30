# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class BlogSettings(Document):
	def on_update(self):
		from dontmanage.website.utils import clear_cache

		clear_cache("blog")
		clear_cache("writers")


def get_like_limit():
	return dontmanage.db.get_single_value("Blog Settings", "like_limit") or 5


def get_comment_limit():
	return dontmanage.db.get_single_value("Blog Settings", "comment_limit") or 5

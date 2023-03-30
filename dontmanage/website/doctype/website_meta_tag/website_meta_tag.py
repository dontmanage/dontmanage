# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class WebsiteMetaTag(Document):
	def get_content(self):
		# can't have new lines in meta content
		return (self.value or "").replace("\n", " ")

	def get_meta_dict(self):
		return {self.key: self.get_content()}

	def set_in_context(self, context):
		context.setdefault("metatags", dontmanage._dict({}))
		context.metatags[self.key] = self.get_content()
		return context

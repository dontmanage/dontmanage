# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class WebsiteScript(Document):
	def on_update(self):
		"""clear cache"""
		dontmanage.clear_cache(user="Guest")

		from dontmanage.website.utils import clear_cache

		clear_cache()

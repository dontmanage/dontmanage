# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class AboutUsSettings(Document):
	def on_update(self):
		from dontmanage.website.utils import clear_cache

		clear_cache("about")


def get_args():
	obj = dontmanage.get_doc("About Us Settings")
	return {"obj": obj}

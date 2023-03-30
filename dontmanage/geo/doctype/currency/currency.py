# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class Currency(Document):
	def validate(self):
		if not dontmanage.flags.in_install_app:
			dontmanage.clear_cache()

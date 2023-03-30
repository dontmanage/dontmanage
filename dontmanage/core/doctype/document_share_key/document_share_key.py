# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

from random import randrange

import dontmanage
from dontmanage.model.document import Document


class DocumentShareKey(Document):
	def before_insert(self):
		self.key = dontmanage.generate_hash(length=randrange(25, 35))
		if not self.expires_on and not self.flags.no_expiry:
			self.expires_on = dontmanage.utils.add_days(
				None, days=dontmanage.get_system_settings("document_share_key_expiry") or 90
			)


def is_expired(expires_on):
	return expires_on and expires_on < dontmanage.utils.getdate()

# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class EmailQueueRecipient(Document):
	DOCTYPE = "Email Queue Recipient"

	def is_mail_to_be_sent(self):
		return self.status == "Not Sent"

	def is_main_sent(self):
		return self.status == "Sent"

	def update_db(self, commit=False, **kwargs):
		dontmanage.db.set_value(self.DOCTYPE, self.name, kwargs)
		if commit:
			dontmanage.db.commit()

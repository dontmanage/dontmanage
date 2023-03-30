# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class EmailGroupMember(Document):
	def after_delete(self):
		email_group = dontmanage.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()

	def after_insert(self):
		email_group = dontmanage.get_doc("Email Group", self.email_group)
		email_group.update_total_subscribers()


def after_doctype_insert():
	dontmanage.db.add_unique("Email Group Member", ("email_group", "email"))

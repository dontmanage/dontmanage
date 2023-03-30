# Copyright (c) 2015, DontManage and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class UnhandledEmail(Document):
	pass


def remove_old_unhandled_emails():
	dontmanage.db.delete(
		"Unhandled Email", {"creation": ("<", dontmanage.utils.add_days(dontmanage.utils.nowdate(), -30))}
	)

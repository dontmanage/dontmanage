# Copyright (c) 2015, DontManage and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document
from dontmanage.query_builder import Interval
from dontmanage.query_builder.functions import Now


class ErrorSnapshot(Document):
	no_feed_on_delete = True

	def onload(self):
		if not self.parent_error_snapshot:
			self.db_set("seen", 1, update_modified=False)

			for relapsed in dontmanage.get_all("Error Snapshot", filters={"parent_error_snapshot": self.name}):
				dontmanage.db.set_value("Error Snapshot", relapsed.name, "seen", 1, update_modified=False)

			dontmanage.local.flags.commit = True

	def validate(self):
		parent = dontmanage.get_all(
			"Error Snapshot",
			filters={"evalue": self.evalue, "parent_error_snapshot": ""},
			fields=["name", "relapses", "seen"],
			limit_page_length=1,
		)

		if parent:
			parent = parent[0]
			self.update({"parent_error_snapshot": parent["name"]})
			dontmanage.db.set_value("Error Snapshot", parent["name"], "relapses", parent["relapses"] + 1)
			if parent["seen"]:
				dontmanage.db.set_value("Error Snapshot", parent["name"], "seen", 0)

	@staticmethod
	def clear_old_logs(days=30):
		table = dontmanage.qb.DocType("Error Snapshot")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))

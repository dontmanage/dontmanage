# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document
from dontmanage.query_builder import Interval
from dontmanage.query_builder.functions import Now


class ErrorLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		error: DF.Code | None
		method: DF.Data | None
		reference_doctype: DF.Link | None
		reference_name: DF.Data | None
		seen: DF.Check
		trace_id: DF.Data | None

	# end: auto-generated types
	def onload(self):
		if not self.seen and not dontmanage.flags.read_only:
			self.db_set("seen", 1, update_modified=0)
			dontmanage.db.commit()

	@staticmethod
	def clear_old_logs(days=30):
		table = dontmanage.qb.DocType("Error Log")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@dontmanage.whitelist()
def clear_error_logs():
	"""Flush all Error Logs"""
	dontmanage.only_for("System Manager")
	dontmanage.db.truncate("Error Log")

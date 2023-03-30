# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document
from dontmanage.query_builder import Interval
from dontmanage.query_builder.functions import Now


class ScheduledJobLog(Document):
	@staticmethod
	def clear_old_logs(days=90):
		table = dontmanage.qb.DocType("Scheduled Job Log")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))

# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document
from dontmanage.query_builder import Interval
from dontmanage.query_builder.functions import Now


class ScheduledJobLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		details: DF.Code | None
		scheduled_job_type: DF.Link
		status: DF.Literal["Scheduled", "Complete", "Failed"]

	# end: auto-generated types
	@staticmethod
	def clear_old_logs(days=90):
		table = dontmanage.qb.DocType("Scheduled Job Log")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))

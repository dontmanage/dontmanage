# Copyright (c) 2021, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class WebhookRequestLog(Document):
	@staticmethod
	def clear_old_logs(days=30):
		from dontmanage.query_builder import Interval
		from dontmanage.query_builder.functions import Now

		table = dontmanage.qb.DocType("Webhook Request Log")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))

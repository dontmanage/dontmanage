# Copyright (c) 2021, DontManage Technologies and contributors
# License: MIT. See LICENSE
from tenacity import retry, retry_if_exception_type, stop_after_attempt

import dontmanage
from dontmanage.model.document import Document
from dontmanage.utils import cstr


class AccessLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		columns: DF.HTMLEditor | None
		export_from: DF.Data | None
		file_type: DF.Data | None
		filters: DF.Code | None
		method: DF.Data | None
		page: DF.HTMLEditor | None
		reference_document: DF.Data | None
		report_name: DF.Data | None
		timestamp: DF.Datetime | None
		user: DF.Link | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		from dontmanage.query_builder import Interval
		from dontmanage.query_builder.functions import Now

		table = dontmanage.qb.DocType("Access Log")
		dontmanage.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))


@dontmanage.whitelist()
@dontmanage.write_only()
@retry(
	stop=stop_after_attempt(3),
	retry=retry_if_exception_type(dontmanage.DuplicateEntryError),
	reraise=True,
)
def make_access_log(
	doctype=None,
	document=None,
	method=None,
	file_type=None,
	report_name=None,
	filters=None,
	page=None,
	columns=None,
):
	access_log = dontmanage.get_doc(
		{
			"doctype": "Access Log",
			"user": dontmanage.session.user,
			"export_from": doctype,
			"reference_document": document,
			"file_type": file_type,
			"report_name": report_name,
			"page": page,
			"method": method,
			"filters": cstr(filters) or None,
			"columns": columns,
		}
	)

	if not dontmanage.in_test:
		access_log.deferred_insert()
	else:
		access_log.db_insert()


# only for backward compatibility
_make_access_log = make_access_log

# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage import _
from dontmanage.desk.doctype.bulk_update.bulk_update import show_progress
from dontmanage.model.document import Document
from dontmanage.model.workflow import get_workflow_name


class DeletedDocument(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		data: DF.Code | None
		deleted_doctype: DF.Data | None
		deleted_name: DF.Data | None
		new_name: DF.ReadOnly | None
		restored: DF.Check
	# end: auto-generated types
	pass

	@staticmethod
	def clear_old_logs(days=180):
		from dontmanage.query_builder import Interval
		from dontmanage.query_builder.functions import Now

		table = dontmanage.qb.DocType("Deleted Document")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@dontmanage.whitelist()
def restore(name, alert=True):
	deleted = dontmanage.get_doc("Deleted Document", name)

	if deleted.restored:
		dontmanage.throw(_("Document {0} Already Restored").format(name), exc=dontmanage.DocumentAlreadyRestored)

	doc = dontmanage.get_doc(json.loads(deleted.data))

	try:
		doc.insert()
	except dontmanage.DocstatusTransitionError:
		dontmanage.msgprint(_("Cancelled Document restored as Draft"))
		doc.docstatus = 0
		active_workflow = get_workflow_name(doc.doctype)
		if active_workflow:
			workflow_state_fieldname = dontmanage.get_value("Workflow", active_workflow, "workflow_state_field")
			if doc.get(workflow_state_fieldname):
				doc.set(workflow_state_fieldname, None)
		doc.insert()

	doc.add_comment("Edit", _("restored {0} as {1}").format(deleted.deleted_name, doc.name))

	deleted.new_name = doc.name
	deleted.restored = 1
	deleted.db_update()

	if alert:
		dontmanage.msgprint(_("Document Restored"))


@dontmanage.whitelist()
def bulk_restore(docnames):
	docnames = dontmanage.parse_json(docnames)
	message = _("Restoring Deleted Document")
	restored, invalid, failed = [], [], []

	for i, d in enumerate(docnames):
		try:
			show_progress(docnames, message, i + 1, d)
			restore(d, alert=False)
			dontmanage.db.commit()
			restored.append(d)

		except dontmanage.DocumentAlreadyRestored:
			dontmanage.clear_last_message()
			invalid.append(d)

		except Exception:
			dontmanage.clear_last_message()
			failed.append(d)
			dontmanage.db.rollback()

	return {"restored": restored, "invalid": invalid, "failed": failed}

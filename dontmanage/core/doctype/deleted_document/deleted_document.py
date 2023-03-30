# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage import _
from dontmanage.desk.doctype.bulk_update.bulk_update import show_progress
from dontmanage.model.document import Document


class DeletedDocument(Document):
	pass


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
			dontmanage.message_log.pop()
			invalid.append(d)

		except Exception:
			dontmanage.message_log.pop()
			failed.append(d)
			dontmanage.db.rollback()

	return {"restored": restored, "invalid": invalid, "failed": failed}

# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.utils import cint


class BulkUpdate(Document):
	pass


@dontmanage.whitelist()
def update(doctype, field, value, condition="", limit=500):
	if not limit or cint(limit) > 500:
		limit = 500

	if condition:
		condition = " where " + condition

	if ";" in condition:
		dontmanage.throw(_("; not allowed in condition"))

	docnames = dontmanage.db.sql_list(
		f"""select name from `tab{doctype}`{condition} limit {limit} offset 0"""
	)
	data = {}
	data[field] = value
	return submit_cancel_or_update_docs(doctype, docnames, "update", data)


@dontmanage.whitelist()
def submit_cancel_or_update_docs(doctype, docnames, action="submit", data=None):
	docnames = dontmanage.parse_json(docnames)

	if data:
		data = dontmanage.parse_json(data)

	failed = []

	for i, d in enumerate(docnames, 1):
		doc = dontmanage.get_doc(doctype, d)
		try:
			message = ""
			if action == "submit" and doc.docstatus.is_draft():
				doc.submit()
				message = _("Submitting {0}").format(doctype)
			elif action == "cancel" and doc.docstatus.is_submitted():
				doc.cancel()
				message = _("Cancelling {0}").format(doctype)
			elif action == "update" and not doc.docstatus.is_cancelled():
				doc.update(data)
				doc.save()
				message = _("Updating {0}").format(doctype)
			else:
				failed.append(d)
			dontmanage.db.commit()
			show_progress(docnames, message, i, d)

		except Exception:
			failed.append(d)
			dontmanage.db.rollback()

	return failed


def show_progress(docnames, message, i, description):
	n = len(docnames)
	if n >= 10:
		dontmanage.publish_progress(float(i) * 100 / n, title=message, description=description)

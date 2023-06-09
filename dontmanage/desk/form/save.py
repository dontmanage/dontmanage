# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage.desk.form.load import run_onload
from dontmanage.model.docstatus import DocStatus
from dontmanage.monitor import add_data_to_monitor


@dontmanage.whitelist()
def savedocs(doc, action):
	"""save / submit / update doclist"""
	doc = dontmanage.get_doc(json.loads(doc))
	set_local_name(doc)

	# action
	doc.docstatus = {
		"Save": DocStatus.draft(),
		"Submit": DocStatus.submitted(),
		"Update": DocStatus.submitted(),
		"Cancel": DocStatus.cancelled(),
	}[action]

	doc.save()

	# update recent documents
	run_onload(doc)
	send_updated_docs(doc)

	add_data_to_monitor(doctype=doc.doctype, action=action)

	dontmanage.msgprint(dontmanage._("Saved"), indicator="green", alert=True)


@dontmanage.whitelist()
def cancel(doctype=None, name=None, workflow_state_fieldname=None, workflow_state=None):
	"""cancel a doclist"""
	doc = dontmanage.get_doc(doctype, name)
	if workflow_state_fieldname and workflow_state:
		doc.set(workflow_state_fieldname, workflow_state)
	doc.cancel()
	send_updated_docs(doc)
	dontmanage.msgprint(dontmanage._("Cancelled"), indicator="red", alert=True)


def send_updated_docs(doc):
	from .load import get_docinfo

	get_docinfo(doc)

	d = doc.as_dict()
	if hasattr(doc, "localname"):
		d["localname"] = doc.localname

	dontmanage.response.docs.append(d)


def set_local_name(doc):
	def _set_local_name(d):
		if doc.get("__islocal") or d.get("__islocal"):
			d.localname = d.name
			d.name = None

	_set_local_name(doc)
	for child in doc.get_all_children():
		_set_local_name(child)

	if doc.get("__newname"):
		doc.name = doc.get("__newname")

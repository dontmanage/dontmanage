import json

from werkzeug.routing import Rule

import dontmanage
from dontmanage import _
from dontmanage.utils.data import sbool


def document_list(doctype: str):
	if dontmanage.form_dict.get("fields"):
		dontmanage.form_dict["fields"] = json.loads(dontmanage.form_dict["fields"])

	# set limit of records for dontmanage.get_list
	dontmanage.form_dict.setdefault(
		"limit_page_length",
		dontmanage.form_dict.limit or dontmanage.form_dict.limit_page_length or 20,
	)

	# convert strings to native types - only as_dict and debug accept bool
	for param in ["as_dict", "debug"]:
		param_val = dontmanage.form_dict.get(param)
		if param_val is not None:
			dontmanage.form_dict[param] = sbool(param_val)

	# evaluate dontmanage.get_list
	return dontmanage.call(dontmanage.client.get_list, doctype, **dontmanage.form_dict)


def handle_rpc_call(method: str):
	import dontmanage.handler

	method = method.split("/")[0]  # for backward compatiblity

	dontmanage.form_dict.cmd = method
	return dontmanage.handler.handle()


def create_doc(doctype: str):
	data = get_request_form_data()
	data.pop("doctype", None)
	return dontmanage.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = get_request_form_data()

	doc = dontmanage.get_doc(doctype, name, for_update=True)
	if "flags" in data:
		del data["flags"]

	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		dontmanage.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	# TODO: child doc handling
	dontmanage.delete_doc(doctype, name, ignore_missing=False)
	dontmanage.response.http_status_code = 202
	return "ok"


def read_doc(doctype: str, name: str):
	# Backward compatiblity
	if "run_method" in dontmanage.form_dict:
		return execute_doc_method(doctype, name)

	doc = dontmanage.get_doc(doctype, name)
	if not doc.has_permission("read"):
		raise dontmanage.PermissionError
	doc.apply_fieldlevel_read_permissions()
	return doc


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	method = method or dontmanage.form_dict.pop("run_method")
	doc = dontmanage.get_doc(doctype, name)
	doc.is_whitelisted(method)

	if dontmanage.request.method == "GET":
		if not doc.has_permission("read"):
			dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)
		return doc.run_method(method, **dontmanage.form_dict)

	elif dontmanage.request.method == "POST":
		if not doc.has_permission("write"):
			dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)

		return doc.run_method(method, **dontmanage.form_dict)


def get_request_form_data():
	if dontmanage.form_dict.data is None:
		data = dontmanage.safe_decode(dontmanage.request.get_data())
	else:
		data = dontmanage.form_dict.data

	try:
		return dontmanage.parse_json(data)
	except ValueError:
		return dontmanage.form_dict


url_rules = [
	Rule("/method/<path:method>", endpoint=handle_rpc_call),
	Rule("/resource/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/resource/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["PUT"], endpoint=update_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["POST"], endpoint=execute_doc_method),
]

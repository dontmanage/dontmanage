# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE

import os
from mimetypes import guess_type
from typing import TYPE_CHECKING

from werkzeug.wrappers import Response

import dontmanage
import dontmanage.sessions
import dontmanage.utils
from dontmanage import _, is_whitelisted, ping
from dontmanage.core.doctype.server_script.server_script_utils import get_server_script_map
from dontmanage.monitor import add_data_to_monitor
from dontmanage.utils import cint
from dontmanage.utils.csvutils import build_csv_response
from dontmanage.utils.deprecations import deprecation_warning
from dontmanage.utils.image import optimize_image
from dontmanage.utils.response import build_response

if TYPE_CHECKING:
	from dontmanage.core.doctype.file.file import File
	from dontmanage.core.doctype.user.user import User

ALLOWED_MIMETYPES = (
	"image/png",
	"image/jpeg",
	"application/pdf",
	"application/msword",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
	"application/vnd.ms-excel",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
	"application/vnd.oasis.opendocument.text",
	"application/vnd.oasis.opendocument.spreadsheet",
	"text/plain",
	"video/quicktime",
	"video/mp4",
)


def handle():
	"""handle request"""

	cmd = dontmanage.local.form_dict.cmd
	data = None

	if cmd != "login":
		data = execute_cmd(cmd)

	# data can be an empty string or list which are valid responses
	if data is not None:
		if isinstance(data, Response):
			# method returns a response object, pass it on
			return data

		# add the response to `message` label
		dontmanage.response["message"] = data


def execute_cmd(cmd, from_async=False):
	"""execute a request as python module"""
	for hook in reversed(dontmanage.get_hooks("override_whitelisted_methods", {}).get(cmd, [])):
		# override using the last hook
		cmd = hook
		break

	# via server script
	server_script = get_server_script_map().get("_api", {}).get(cmd)
	if server_script:
		return run_server_script(server_script)

	try:
		method = get_attr(cmd)
	except Exception as e:
		dontmanage.throw(_("Failed to get method for command {0} with {1}").format(cmd, e))

	if from_async:
		method = method.queue

	if method != run_doc_method:
		is_whitelisted(method)
		is_valid_http_method(method)

	return dontmanage.call(method, **dontmanage.form_dict)


def run_server_script(server_script):
	response = dontmanage.get_doc("Server Script", server_script).execute_method()

	# some server scripts return output using flags (empty dict by default),
	# while others directly modify dontmanage.response
	# return flags if not empty dict (this overwrites dontmanage.response.message)
	if response != {}:
		return response


def is_valid_http_method(method):
	if dontmanage.flags.in_safe_exec:
		return

	http_method = dontmanage.local.request.method

	if http_method not in dontmanage.allowed_http_methods_for_whitelisted_func[method]:
		throw_permission_error()


def throw_permission_error():
	dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)


@dontmanage.whitelist(allow_guest=True)
def logout():
	dontmanage.local.login_manager.logout()
	dontmanage.db.commit()


@dontmanage.whitelist(allow_guest=True)
def web_logout():
	dontmanage.local.login_manager.logout()
	dontmanage.db.commit()
	dontmanage.respond_as_web_page(
		_("Logged Out"), _("You have been successfully logged out"), indicator_color="green"
	)


@dontmanage.whitelist()
def uploadfile():
	ret = None
	check_write_permission(dontmanage.form_dict.doctype, dontmanage.form_dict.docname)

	try:
		if dontmanage.form_dict.get("from_form"):
			try:
				ret = dontmanage.get_doc(
					{
						"doctype": "File",
						"attached_to_name": dontmanage.form_dict.docname,
						"attached_to_doctype": dontmanage.form_dict.doctype,
						"attached_to_field": dontmanage.form_dict.docfield,
						"file_url": dontmanage.form_dict.file_url,
						"file_name": dontmanage.form_dict.filename,
						"is_private": dontmanage.utils.cint(dontmanage.form_dict.is_private),
						"content": dontmanage.form_dict.filedata,
						"decode": True,
					}
				)
				ret.save()
			except dontmanage.DuplicateEntryError:
				# ignore pass
				ret = None
				dontmanage.db.rollback()
		else:
			if dontmanage.form_dict.get("method"):
				method = dontmanage.get_attr(dontmanage.form_dict.method)
				is_whitelisted(method)
				ret = method()
	except Exception:
		dontmanage.errprint(dontmanage.utils.get_traceback())
		dontmanage.response["http_status_code"] = 500
		ret = None

	return ret


@dontmanage.whitelist(allow_guest=True)
def upload_file():
	user = None
	if dontmanage.session.user == "Guest":
		if dontmanage.get_system_settings("allow_guests_to_upload_files"):
			ignore_permissions = True
		else:
			raise dontmanage.PermissionError
	else:
		user: "User" = dontmanage.get_doc("User", dontmanage.session.user)
		ignore_permissions = False

	files = dontmanage.request.files
	is_private = dontmanage.form_dict.is_private
	doctype = dontmanage.form_dict.doctype
	docname = dontmanage.form_dict.docname
	fieldname = dontmanage.form_dict.fieldname
	file_url = dontmanage.form_dict.file_url
	folder = dontmanage.form_dict.folder or "Home"
	method = dontmanage.form_dict.method
	filename = dontmanage.form_dict.file_name
	optimize = dontmanage.form_dict.optimize
	content = None

	if library_file := dontmanage.form_dict.get("library_file_name"):
		dontmanage.has_permission("File", doc=library_file, throw=True)
		doc = dontmanage.get_value(
			"File",
			dontmanage.form_dict.library_file_name,
			["is_private", "file_url", "file_name"],
			as_dict=True,
		)
		is_private = doc.is_private
		file_url = doc.file_url
		filename = doc.file_name

	if not ignore_permissions:
		check_write_permission(doctype, docname)

	if "file" in files:
		file = files["file"]
		content = file.stream.read()
		filename = file.filename

		content_type = guess_type(filename)[0]
		if optimize and content_type and content_type.startswith("image/"):
			args = {"content": content, "content_type": content_type}
			if dontmanage.form_dict.max_width:
				args["max_width"] = int(dontmanage.form_dict.max_width)
			if dontmanage.form_dict.max_height:
				args["max_height"] = int(dontmanage.form_dict.max_height)
			content = optimize_image(**args)

	dontmanage.local.uploaded_file = content
	dontmanage.local.uploaded_filename = filename

	if content is not None and (dontmanage.session.user == "Guest" or (user and not user.has_desk_access())):
		filetype = guess_type(filename)[0]
		if filetype not in ALLOWED_MIMETYPES:
			dontmanage.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

	if method:
		method = dontmanage.get_attr(method)
		is_whitelisted(method)
		return method()
	else:
		return dontmanage.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": doctype,
				"attached_to_name": docname,
				"attached_to_field": fieldname,
				"folder": folder,
				"file_name": filename,
				"file_url": file_url,
				"is_private": cint(is_private),
				"content": content,
			}
		).save(ignore_permissions=ignore_permissions)


def check_write_permission(doctype: str | None = None, name: str | None = None):
	check_doctype = doctype and not name
	if doctype and name:
		try:
			doc = dontmanage.get_doc(doctype, name)
			doc.has_permission("write")
		except dontmanage.DoesNotExistError:
			# doc has not been inserted yet, name is set to "new-some-doctype"
			check_doctype = True

	if check_doctype:
		dontmanage.has_permission(doctype, "write", throw=True)


@dontmanage.whitelist(allow_guest=True)
def download_file(file_url: str):
	"""
	Download file using token and REST API. Valid session or
	token is required to download private files.

	Method : GET
	Endpoints : download_file, dontmanage.core.doctype.file.file.download_file
	URL Params : file_name = /path/to/file relative to site path
	"""
	file: "File" = dontmanage.get_doc("File", {"file_url": file_url})
	if not file.is_downloadable():
		raise dontmanage.PermissionError

	dontmanage.local.response.filename = os.path.basename(file_url)
	dontmanage.local.response.filecontent = file.get_content()
	dontmanage.local.response.type = "download"


def get_attr(cmd):
	"""get method object from cmd"""
	if "." in cmd:
		method = dontmanage.get_attr(cmd)
	else:
		deprecation_warning(
			f"Calling shorthand for {cmd} is deprecated, please specify full path in RPC call."
		)
		method = globals()[cmd]
	dontmanage.log("method:" + cmd)
	return method


def run_doc_method(method, docs=None, dt=None, dn=None, arg=None, args=None):
	"""run a whitelisted controller method"""
	from inspect import signature

	if not args and arg:
		args = arg

	if dt:  # not called from a doctype (from a page)
		if not dn:
			dn = dt  # single
		doc = dontmanage.get_doc(dt, dn)

	else:
		docs = dontmanage.parse_json(docs)
		doc = dontmanage.get_doc(docs)
		doc._original_modified = doc.modified
		doc.check_if_latest()

	if not doc or not doc.has_permission("read"):
		throw_permission_error()

	try:
		args = dontmanage.parse_json(args)
	except ValueError:
		pass

	method_obj = getattr(doc, method)
	fn = getattr(method_obj, "__func__", method_obj)
	is_whitelisted(fn)
	is_valid_http_method(fn)

	fnargs = list(signature(method_obj).parameters)

	if not fnargs or (len(fnargs) == 1 and fnargs[0] == "self"):
		response = doc.run_method(method)

	elif "args" in fnargs or not isinstance(args, dict):
		response = doc.run_method(method, args)

	else:
		response = doc.run_method(method, **args)

	dontmanage.response.docs.append(doc)
	if response is None:
		return

	# build output as csv
	if cint(dontmanage.form_dict.get("as_csv")):
		build_csv_response(response, _(doc.doctype).replace(" ", ""))
		return

	dontmanage.response["message"] = response

	add_data_to_monitor(methodname=method)


# for backwards compatibility
runserverobj = run_doc_method

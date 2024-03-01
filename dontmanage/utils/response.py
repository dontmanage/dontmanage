# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE

import datetime
import decimal
import json
import mimetypes
import os
import sys
from typing import TYPE_CHECKING
from urllib.parse import quote

import werkzeug.utils
from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.local import LocalProxy
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

import dontmanage
import dontmanage.model.document
import dontmanage.sessions
import dontmanage.utils
from dontmanage import _
from dontmanage.core.doctype.access_log.access_log import make_access_log
from dontmanage.utils import format_timedelta

if TYPE_CHECKING:
	from dontmanage.core.doctype.file.file import File


def report_error(status_code):
	"""Build error. Show traceback in developer mode"""
	from dontmanage.api import ApiVersion, get_api_version

	allow_traceback = (
		(dontmanage.get_system_settings("allow_error_traceback") if dontmanage.db else False)
		and not dontmanage.local.flags.disable_traceback
		and (status_code != 404 or dontmanage.conf.logging)
	)

	traceback = dontmanage.utils.get_traceback()
	exc_type, exc_value, _ = sys.exc_info()

	match get_api_version():
		case ApiVersion.V1:
			if allow_traceback:
				dontmanage.errprint(traceback)
				dontmanage.response.exception = traceback.splitlines()[-1]
			dontmanage.response["exc_type"] = exc_type.__name__
		case ApiVersion.V2:
			error_log = {"type": exc_type.__name__}
			if allow_traceback:
				error_log["exception"] = traceback
			_link_error_with_message_log(error_log, exc_value, dontmanage.message_log)
			dontmanage.local.response.errors = [error_log]

	response = build_response("json")
	response.status_code = status_code

	return response


def _link_error_with_message_log(error_log, exception, message_logs):
	for message in list(message_logs):
		if message.get("__dontmanage_exc_id") == getattr(exception, "__dontmanage_exc_id", None):
			error_log.update(message)
			message_logs.remove(message)
			error_log.pop("raise_exception", None)
			error_log.pop("__dontmanage_exc_id", None)
			return


def build_response(response_type=None):
	if "docs" in dontmanage.local.response and not dontmanage.local.response.docs:
		del dontmanage.local.response["docs"]

	response_type_map = {
		"csv": as_csv,
		"txt": as_txt,
		"download": as_raw,
		"json": as_json,
		"pdf": as_pdf,
		"page": as_page,
		"redirect": redirect,
		"binary": as_binary,
	}

	return response_type_map[dontmanage.response.get("type") or response_type]()


def as_csv():
	response = Response()
	response.mimetype = "text/csv"
	filename = f"{dontmanage.response['doctype']}.csv"
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", "attachment", filename=filename)
	response.data = dontmanage.response["result"]
	return response


def as_txt():
	response = Response()
	response.mimetype = "text"
	filename = f"{dontmanage.response['doctype']}.txt"
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", "attachment", filename=filename)
	response.data = dontmanage.response["result"]
	return response


def as_raw():
	response = Response()
	response.mimetype = (
		dontmanage.response.get("content_type")
		or mimetypes.guess_type(dontmanage.response["filename"])[0]
		or "application/unknown"
	)
	filename = dontmanage.response["filename"].encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add(
		"Content-Disposition",
		dontmanage.response.get("display_content_as", "attachment"),
		filename=filename,
	)
	response.data = dontmanage.response["filecontent"]
	return response


def as_json():
	make_logs()

	response = Response()
	if dontmanage.local.response.http_status_code:
		response.status_code = dontmanage.local.response["http_status_code"]
		del dontmanage.local.response["http_status_code"]

	response.mimetype = "application/json"
	response.data = json.dumps(dontmanage.local.response, default=json_handler, separators=(",", ":"))
	return response


def as_pdf():
	response = Response()
	response.mimetype = "application/pdf"
	filename = dontmanage.response["filename"].encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", None, filename=filename)
	response.data = dontmanage.response["filecontent"]
	return response


def as_binary():
	response = Response()
	response.mimetype = "application/octet-stream"
	filename = dontmanage.response["filename"]
	filename = filename.encode("utf-8").decode("unicode-escape", "ignore")
	response.headers.add("Content-Disposition", None, filename=filename)
	response.data = dontmanage.response["filecontent"]
	return response


def make_logs():
	"""make strings for msgprint and errprint"""

	from dontmanage.api import ApiVersion, get_api_version

	match get_api_version():
		case ApiVersion.V1:
			_make_logs_v1()
		case ApiVersion.V2:
			_make_logs_v2()


def _make_logs_v1():
	from dontmanage.utils.error import guess_exception_source

	response = dontmanage.local.response
	allow_traceback = dontmanage.get_system_settings("allow_error_traceback") if dontmanage.db else False

	if dontmanage.error_log and allow_traceback:
		if source := guess_exception_source(dontmanage.local.error_log and dontmanage.local.error_log[0]["exc"]):
			response["_exc_source"] = source
		response["exc"] = json.dumps([dontmanage.utils.cstr(d["exc"]) for d in dontmanage.local.error_log])

	if dontmanage.local.message_log:
		response["_server_messages"] = json.dumps([json.dumps(d) for d in dontmanage.local.message_log])

	if dontmanage.debug_log and dontmanage.conf.get("logging"):
		response["_debug_messages"] = json.dumps(dontmanage.local.debug_log)

	if dontmanage.flags.error_message:
		response["_error_message"] = dontmanage.flags.error_message


def _make_logs_v2():
	response = dontmanage.local.response

	if dontmanage.local.message_log:
		response["messages"] = dontmanage.local.message_log

	if dontmanage.debug_log and dontmanage.conf.get("logging"):
		response["debug"] = [{"message": m} for m in dontmanage.local.debug_log]


def json_handler(obj):
	"""serialize non-serializable data for json"""
	from collections.abc import Iterable
	from re import Match

	if isinstance(obj, datetime.date | datetime.datetime | datetime.time):
		return str(obj)

	elif isinstance(obj, datetime.timedelta):
		return format_timedelta(obj)

	elif isinstance(obj, decimal.Decimal):
		return float(obj)

	elif isinstance(obj, LocalProxy):
		return str(obj)

	elif isinstance(obj, dontmanage.model.document.BaseDocument):
		return obj.as_dict(no_nulls=True)
	elif isinstance(obj, Iterable):
		return list(obj)

	elif isinstance(obj, Match):
		return obj.string

	elif type(obj) == type or isinstance(obj, Exception):
		return repr(obj)

	elif callable(obj):
		return repr(obj)

	else:
		raise TypeError(f"""Object of type {type(obj)} with value of {obj!r} is not JSON serializable""")


def as_page():
	"""print web page"""
	from dontmanage.website.serve import get_response

	return get_response(dontmanage.response["route"], http_status_code=dontmanage.response.get("http_status_code"))


def redirect():
	return werkzeug.utils.redirect(dontmanage.response.location)


def download_backup(path):
	try:
		dontmanage.only_for(("System Manager", "Administrator"))
		make_access_log(report_name="Backup")
	except dontmanage.PermissionError:
		raise Forbidden(
			_("You need to be logged in and have System Manager Role to be able to access backups.")
		)

	return send_private_file(path)


def download_private_file(path: str) -> Response:
	"""Checks permissions and sends back private file"""
	from dontmanage.core.doctype.file.utils import find_file_by_url

	if dontmanage.session.user == "Guest":
		raise Forbidden(_("You don't have permission to access this file"))

	file = find_file_by_url(path, name=dontmanage.form_dict.fid)
	if not file:
		raise Forbidden(_("You don't have permission to access this file"))

	make_access_log(doctype="File", document=file.name, file_type=os.path.splitext(path)[-1][1:])
	return send_private_file(path.split("/private", 1)[1])


def send_private_file(path: str) -> Response:
	path = os.path.join(dontmanage.local.conf.get("private_path", "private"), path.strip("/"))
	filename = os.path.basename(path)

	if dontmanage.local.request.headers.get("X-Use-X-Accel-Redirect"):
		path = "/protected/" + path
		response = Response()
		response.headers["X-Accel-Redirect"] = quote(dontmanage.utils.encode(path))

	else:
		filepath = dontmanage.utils.get_site_path(path)
		try:
			f = open(filepath, "rb")
		except OSError:
			raise NotFound

		response = Response(wrap_file(dontmanage.local.request.environ, f), direct_passthrough=True)

	# no need for content disposition and force download. let browser handle its opening.
	# Except for those that can be injected with scripts.

	extension = os.path.splitext(path)[1]
	blacklist = [".svg", ".html", ".htm", ".xml"]

	if extension.lower() in blacklist:
		response.headers.add("Content-Disposition", "attachment", filename=filename)

	response.mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

	return response


def handle_session_stopped():
	from dontmanage.website.serve import get_response

	dontmanage.respond_as_web_page(
		_("Updating"),
		_("The system is being updated. Please refresh again after a few moments."),
		http_status_code=503,
		indicator_color="orange",
		fullpage=True,
		primary_action=None,
	)
	return get_response("message", http_status_code=503)

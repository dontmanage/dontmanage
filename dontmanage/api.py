# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import base64
import binascii
import json
from urllib.parse import urlencode, urlparse

import dontmanage
import dontmanage.client
import dontmanage.handler
from dontmanage import _
from dontmanage.utils.data import sbool
from dontmanage.utils.response import build_response


def handle():
	"""
	Handler for `/api` methods

	### Examples:

	`/api/method/{methodname}` will call a whitelisted method

	`/api/resource/{doctype}` will query a table
	        examples:
	        - `?fields=["name", "owner"]`
	        - `?filters=[["Task", "name", "like", "%005"]]`
	        - `?limit_start=0`
	        - `?limit_page_length=20`

	`/api/resource/{doctype}/{name}` will point to a resource
	        `GET` will return doclist
	        `POST` will insert
	        `PUT` will update
	        `DELETE` will delete

	`/api/resource/{doctype}/{name}?run_method={method}` will run a whitelisted controller method
	"""

	parts = dontmanage.request.path[1:].split("/", 3)
	call = doctype = name = None

	if len(parts) > 1:
		call = parts[1]

	if len(parts) > 2:
		doctype = parts[2]

	if len(parts) > 3:
		name = parts[3]

	if call == "method":
		dontmanage.local.form_dict.cmd = doctype
		return dontmanage.handler.handle()

	elif call == "resource":
		if "run_method" in dontmanage.local.form_dict:
			method = dontmanage.local.form_dict.pop("run_method")
			doc = dontmanage.get_doc(doctype, name)
			doc.is_whitelisted(method)

			if dontmanage.local.request.method == "GET":
				if not doc.has_permission("read"):
					dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)
				dontmanage.local.response.update({"data": doc.run_method(method, **dontmanage.local.form_dict)})

			if dontmanage.local.request.method == "POST":
				if not doc.has_permission("write"):
					dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)

				dontmanage.local.response.update({"data": doc.run_method(method, **dontmanage.local.form_dict)})
				dontmanage.db.commit()

		else:
			if name:
				if dontmanage.local.request.method == "GET":
					doc = dontmanage.get_doc(doctype, name)
					if not doc.has_permission("read"):
						raise dontmanage.PermissionError
					if dontmanage.get_system_settings("apply_perm_level_on_api_calls"):
						doc.apply_fieldlevel_read_permissions()
					dontmanage.local.response.update({"data": doc})

				if dontmanage.local.request.method == "PUT":
					data = get_request_form_data()

					doc = dontmanage.get_doc(doctype, name, for_update=True)

					if "flags" in data:
						del data["flags"]

					# Not checking permissions here because it's checked in doc.save
					doc.update(data)
					doc.save()
					if dontmanage.get_system_settings("apply_perm_level_on_api_calls"):
						doc.apply_fieldlevel_read_permissions()
					dontmanage.local.response.update({"data": doc})

					# check for child table doctype
					if doc.get("parenttype"):
						dontmanage.get_doc(doc.parenttype, doc.parent).save()

					dontmanage.db.commit()

				if dontmanage.local.request.method == "DELETE":
					# Not checking permissions here because it's checked in delete_doc
					dontmanage.delete_doc(doctype, name, ignore_missing=False)
					dontmanage.local.response.http_status_code = 202
					dontmanage.local.response.message = "ok"
					dontmanage.db.commit()

			elif doctype:
				if dontmanage.local.request.method == "GET":
					# set fields for dontmanage.get_list
					if dontmanage.local.form_dict.get("fields"):
						dontmanage.local.form_dict["fields"] = json.loads(dontmanage.local.form_dict["fields"])

					# set limit of records for dontmanage.get_list
					dontmanage.local.form_dict.setdefault(
						"limit_page_length",
						dontmanage.local.form_dict.limit or dontmanage.local.form_dict.limit_page_length or 20,
					)

					# convert strings to native types - only as_dict and debug accept bool
					for param in ["as_dict", "debug"]:
						param_val = dontmanage.local.form_dict.get(param)
						if param_val is not None:
							dontmanage.local.form_dict[param] = sbool(param_val)

					# evaluate dontmanage.get_list
					data = dontmanage.call(dontmanage.client.get_list, doctype, **dontmanage.local.form_dict)

					# set dontmanage.get_list result to response
					dontmanage.local.response.update({"data": data})

				if dontmanage.local.request.method == "POST":
					# fetch data from from dict
					data = get_request_form_data()
					data.update({"doctype": doctype})

					# insert document from request data
					doc = dontmanage.get_doc(data).insert()

					# set response data
					dontmanage.local.response.update({"data": doc.as_dict()})

					# commit for POST requests
					dontmanage.db.commit()
			else:
				raise dontmanage.DoesNotExistError

	else:
		raise dontmanage.DoesNotExistError

	return build_response("json")


def get_request_form_data():
	if dontmanage.local.form_dict.data is None:
		data = dontmanage.safe_decode(dontmanage.local.request.get_data())
	else:
		data = dontmanage.local.form_dict.data

	try:
		return dontmanage.parse_json(data)
	except ValueError:
		return dontmanage.local.form_dict


def validate_auth():
	"""
	Authenticate and sets user for the request.
	"""
	authorization_header = dontmanage.get_request_header("Authorization", "").split(" ")

	if len(authorization_header) == 2:
		validate_oauth(authorization_header)
		validate_auth_via_api_keys(authorization_header)

	validate_auth_via_hooks()


def validate_oauth(authorization_header):
	"""
	Authenticate request using OAuth and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	from dontmanage.integrations.oauth2 import get_oauth_server
	from dontmanage.oauth import get_url_delimiter

	form_dict = dontmanage.local.form_dict
	token = authorization_header[1]
	req = dontmanage.request
	parsed_url = urlparse(req.url)
	access_token = {"access_token": token}
	uri = (
		parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
	)
	http_method = req.method
	headers = req.headers
	body = req.get_data()
	if req.content_type and "multipart/form-data" in req.content_type:
		body = None

	try:
		required_scopes = dontmanage.db.get_value("OAuth Bearer Token", token, "scopes").split(
			get_url_delimiter()
		)
		valid, oauthlib_request = get_oauth_server().verify_request(
			uri, http_method, body, headers, required_scopes
		)
		if valid:
			dontmanage.set_user(dontmanage.db.get_value("OAuth Bearer Token", token, "user"))
			dontmanage.local.form_dict = form_dict
	except AttributeError:
		pass


def validate_auth_via_api_keys(authorization_header):
	"""
	Authenticate request using API keys and set session user

	Args:
	        authorization_header (list of str): The 'Authorization' header containing the prefix and token
	"""

	try:
		auth_type, auth_token = authorization_header
		authorization_source = dontmanage.get_request_header("DontManage-Authorization-Source")
		if auth_type.lower() == "basic":
			api_key, api_secret = dontmanage.safe_decode(base64.b64decode(auth_token)).split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
		elif auth_type.lower() == "token":
			api_key, api_secret = auth_token.split(":")
			validate_api_key_secret(api_key, api_secret, authorization_source)
	except binascii.Error:
		dontmanage.throw(
			_("Failed to decode token, please provide a valid base64-encoded token."),
			dontmanage.InvalidAuthorizationToken,
		)
	except (AttributeError, TypeError, ValueError):
		pass


def validate_api_key_secret(api_key, api_secret, dontmanage_authorization_source=None):
	"""dontmanage_authorization_source to provide api key and secret for a doctype apart from User"""
	doctype = dontmanage_authorization_source or "User"
	doc = dontmanage.db.get_value(doctype=doctype, filters={"api_key": api_key}, fieldname=["name"])
	form_dict = dontmanage.local.form_dict
	doc_secret = dontmanage.utils.password.get_decrypted_password(doctype, doc, fieldname="api_secret")
	if api_secret == doc_secret:
		if doctype == "User":
			user = dontmanage.db.get_value(doctype="User", filters={"api_key": api_key}, fieldname=["name"])
		else:
			user = dontmanage.db.get_value(doctype, doc, "user")
		if dontmanage.local.login_manager.user in ("", "Guest"):
			dontmanage.set_user(user)
		dontmanage.local.form_dict = form_dict


def validate_auth_via_hooks():
	for auth_hook in dontmanage.get_hooks("auth_hooks", []):
		dontmanage.get_attr(auth_hook)()

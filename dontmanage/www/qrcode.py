# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

from urllib.parse import parse_qsl

import dontmanage
from dontmanage import _
from dontmanage.twofactor import get_qr_svg_code


def get_context(context):
	context.no_cache = 1
	context.qr_code_user, context.qrcode_svg = get_user_svg_from_cache()


def get_query_key():
	"""Return query string arg."""
	query_string = dontmanage.local.request.query_string
	query = dict(parse_qsl(query_string))
	query = {key.decode(): val.decode() for key, val in query.items()}
	if not "k" in list(query):
		dontmanage.throw(_("Not Permitted"), dontmanage.PermissionError)
	query = (query["k"]).strip()
	if False in [i.isalpha() or i.isdigit() for i in query]:
		dontmanage.throw(_("Not Permitted"), dontmanage.PermissionError)
	return query


def get_user_svg_from_cache():
	"""Get User and SVG code from cache."""
	key = get_query_key()
	totp_uri = dontmanage.cache().get_value(f"{key}_uri")
	user = dontmanage.cache().get_value(f"{key}_user")
	if not totp_uri or not user:
		dontmanage.throw(_("Page has expired!"), dontmanage.PermissionError)
	if not dontmanage.db.exists("User", user):
		dontmanage.throw(_("Not Permitted"), dontmanage.PermissionError)
	user = dontmanage.get_doc("User", user)
	svg = get_qr_svg_code(totp_uri)
	return (user, svg.decode())

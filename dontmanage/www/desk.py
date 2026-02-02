# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import os

no_cache = 1

import json
import re
from urllib.parse import urlencode

import dontmanage
import dontmanage.sessions
from dontmanage import _
from dontmanage.utils.jinja_globals import is_rtl

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


def get_context(context):
	if dontmanage.session.user == "Guest":
		dontmanage.response["status_code"] = 403
		dontmanage.msgprint(_("Log in to access this page."))
		dontmanage.redirect(f"/login?{urlencode({'redirect-to': dontmanage.request.path})}")

	elif dontmanage.session.data.user_type == "Website User":
		dontmanage.throw(_("You are not permitted to access this page."), dontmanage.PermissionError)

	try:
		boot = dontmanage.sessions.get()
	except Exception as e:
		raise dontmanage.SessionBootFailed from e

	# this needs commit
	csrf_token = dontmanage.sessions.get_csrf_token()

	hooks = dontmanage.get_hooks()
	app_include_js = hooks.get("app_include_js", []) + dontmanage.conf.get("app_include_js", [])
	app_include_css = hooks.get("app_include_css", []) + dontmanage.conf.get("app_include_css", [])
	app_include_icons = hooks.get("app_include_icons", [])

	if dontmanage.get_system_settings("enable_telemetry") and os.getenv("DONTMANAGE_SENTRY_DSN"):
		app_include_js.append("sentry.bundle.js")

	context.update(
		{
			"no_cache": 1,
			"build_version": dontmanage.utils.get_build_version(),
			"app_include_js": app_include_js,
			"app_include_css": app_include_css,
			"app_include_icons": app_include_icons,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": dontmanage.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot,
			"desk_theme": boot.get("desk_theme") or "Light",
			"csrf_token": csrf_token,
			"google_analytics_id": dontmanage.conf.get("google_analytics_id"),
			"google_analytics_anonymize_ip": dontmanage.conf.get("google_analytics_anonymize_ip"),
			"app_name": (
				dontmanage.get_website_settings("app_name") or dontmanage.get_system_settings("app_name") or "DontManage"
			),
		}
	)

	return context

# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import os

no_cache = 1

import json
import re

import dontmanage
import dontmanage.sessions
from dontmanage import _
from dontmanage.utils.jinja_globals import is_rtl

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


def get_context(context):
	if dontmanage.session.user == "Guest":
		dontmanage.throw(_("Log in to access this page."), dontmanage.PermissionError)
	elif dontmanage.db.get_value("User", dontmanage.session.user, "user_type", order_by=None) == "Website User":
		dontmanage.throw(_("You are not permitted to access this page."), dontmanage.PermissionError)

	hooks = dontmanage.get_hooks()
	try:
		boot = dontmanage.sessions.get()
	except Exception as e:
		raise dontmanage.SessionBootFailed from e

	# this needs commit
	csrf_token = dontmanage.sessions.get_csrf_token()

	dontmanage.db.commit()

	boot_json = dontmanage.as_json(boot, indent=None, separators=(",", ":"))

	# remove script tags from boot
	boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)

	# TODO: Find better fix
	boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = json.dumps(boot_json)

	include_js = hooks.get("app_include_js", []) + dontmanage.conf.get("app_include_js", [])
	include_css = hooks.get("app_include_css", []) + dontmanage.conf.get("app_include_css", [])
	include_icons = hooks.get("app_include_icons", [])
	dontmanage.local.preload_assets["icons"].extend(include_icons)

	if dontmanage.get_system_settings("enable_telemetry") and os.getenv("DONTMANAGE_SENTRY_DSN"):
		include_js.append("sentry.bundle.js")

	context.update(
		{
			"no_cache": 1,
			"build_version": dontmanage.utils.get_build_version(),
			"include_js": include_js,
			"include_css": include_css,
			"include_icons": include_icons,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": dontmanage.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot if context.get("for_mobile") else boot_json,
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

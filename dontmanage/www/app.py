# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
no_cache = 1

import json
import os
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
	elif (
		dontmanage.db.get_value("User", dontmanage.session.user, "user_type", order_by=None) == "Website User"
	):
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

	context.update(
		{
			"no_cache": 1,
			"build_version": dontmanage.utils.get_build_version(),
			"include_js": include_js,
			"include_css": include_css,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": dontmanage.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot if context.get("for_mobile") else boot_json,
			"desk_theme": boot.get("desk_theme") or "Light",
			"csrf_token": csrf_token,
			"google_analytics_id": dontmanage.conf.get("google_analytics_id"),
			"google_analytics_anonymize_ip": dontmanage.conf.get("google_analytics_anonymize_ip"),
			"mixpanel_id": dontmanage.conf.get("mixpanel_id"),
		}
	)

	return context


@dontmanage.whitelist()
def get_desk_assets(build_version):
	"""Get desk assets to be loaded for mobile app"""
	data = get_context({"for_mobile": True})
	assets = [{"type": "js", "data": ""}, {"type": "css", "data": ""}]

	if build_version != data["build_version"]:
		# new build, send assets
		for path in data["include_js"]:
			# assets path shouldn't start with /
			# as it points to different location altogether
			if path.startswith("/assets/"):
				path = path.replace("/assets/", "assets/")
			try:
				with open(os.path.join(dontmanage.local.sites_path, path)) as f:
					assets[0]["data"] = assets[0]["data"] + "\n" + dontmanage.safe_decode(f.read(), "utf-8")
			except OSError:
				pass

		for path in data["include_css"]:
			if path.startswith("/assets/"):
				path = path.replace("/assets/", "assets/")
			try:
				with open(os.path.join(dontmanage.local.sites_path, path)) as f:
					assets[1]["data"] = assets[1]["data"] + "\n" + dontmanage.safe_decode(f.read(), "utf-8")
			except OSError:
				pass

	return {"build_version": data["build_version"], "boot": data["boot"], "assets": assets}

import sys

import dontmanage
from dontmanage.desk.doctype.desktop_icon.desktop_icon import get_desktop_icons


def get_context(context):
	if dontmanage.session.user == "Guest":
		dontmanage.local.flags.redirect_location = "/app"
		raise dontmanage.Redirect
	brand_logo = None
	brand_logo = dontmanage.get_single_value("Navbar Settings", "app_logo")
	if not brand_logo:
		brand_logo = dontmanage.get_hooks("app_logo_url", app_name="dontmanage")[0]
	context.brand_logo = brand_logo
	try:
		context.desktop_layout = dontmanage.get_doc("Desktop Layout", dontmanage.session.user).layout or {}
	except dontmanage.DoesNotExistError:
		dontmanage.clear_last_message()
		context.desktop_layout = {}
	return context

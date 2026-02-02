import dontmanage
from dontmanage.utils import get_app_version, get_dontmanage_version

from .client import capture, is_enabled


def capture_app_heartbeat(app):
	if not should_capture():
		return

	if app and app != "dontmanage":
		capture(
			event_name="app_heartbeat",
			site=dontmanage.local.site,
			app=app,
			properties={
				"app_version": get_app_version(app),
				"dontmanage_version": get_dontmanage_version(),
			},
			interval="6h",
		)


def should_capture():
	if not is_enabled() or dontmanage.session.user in dontmanage.STANDARD_USERS:
		return False

	status_code = dontmanage.response.http_status_code or 0
	if status_code and not (200 <= status_code < 300):
		return False

	return True

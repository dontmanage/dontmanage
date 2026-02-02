from contextlib import suppress
from functools import lru_cache

import dontmanage
from dontmanage.utils.caching import site_cache

from posthog import Posthog  # isort: skip

POSTHOG_PROJECT_FIELD = "posthog_project_id"
POSTHOG_HOST_FIELD = "posthog_host"


def is_enabled():
	return bool(
		dontmanage.conf.get(POSTHOG_HOST_FIELD)
		and dontmanage.conf.get(POSTHOG_PROJECT_FIELD)
		and dontmanage.get_system_settings("enable_telemetry")
	)


def init_telemetry():
	"""Init posthog for server side telemetry."""
	if hasattr(dontmanage.local, "posthog"):
		return

	if not is_enabled():
		return

	posthog_host = dontmanage.conf.get(POSTHOG_HOST_FIELD)
	posthog_project_id = dontmanage.conf.get(POSTHOG_PROJECT_FIELD)

	with suppress(Exception):
		dontmanage.local.posthog = _get_posthog_instance(posthog_project_id, posthog_host)

	# Background jobs might exit before flushing telemetry, so explicitly flush queue
	if dontmanage.job:
		dontmanage.job.after_job.add(flush_telemetry)


@lru_cache
def _get_posthog_instance(project_id, host):
	return Posthog(project_id, host=host, timeout=5, max_retries=3)


def flush_telemetry():
	ph: Posthog = getattr(dontmanage.local, "posthog", None)
	with suppress(Exception):
		ph and ph.flush()


def capture(event, app, **kwargs):
	init_telemetry()
	ph: Posthog = getattr(dontmanage.local, "posthog", None)
	with suppress(Exception):
		ph and ph.capture(distinct_id=dontmanage.local.site, event=f"{app}_{event}", **kwargs)


def capture_doc(doc, action):
	from dontmanage.utils.telemetry import site_age

	with suppress(Exception):
		age = site_age()
		if not age or age > 15:
			return

		if doc.get("__islocal") or not doc.get("name"):
			capture("document_created", "dontmanage", properties={"doctype": doc.doctype, "action": "Insert"})
		else:
			capture("document_modified", "dontmanage", properties={"doctype": doc.doctype, "action": action})

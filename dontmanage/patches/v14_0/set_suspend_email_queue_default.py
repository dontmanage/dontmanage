import dontmanage
from dontmanage.cache_manager import clear_defaults_cache


def execute():
	dontmanage.db.set_default(
		"suspend_email_queue",
		dontmanage.db.get_default("hold_queue", "Administrator") or 0,
		parent="__default",
	)

	dontmanage.db.delete("DefaultValue", {"defkey": "hold_queue"})
	clear_defaults_cache()

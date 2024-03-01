# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage import _

no_cache = 1


def get_context(context):
	if dontmanage.flags.in_migrate:
		return

	allow_traceback = dontmanage.get_system_settings("allow_error_traceback") if dontmanage.db else False

	context.error_title = context.error_title or _("Uncaught Server Exception")
	context.error_message = context.error_message or _("There was an error building this page")

	return {
		"error": dontmanage.get_traceback().replace("<", "&lt;").replace(">", "&gt;") if allow_traceback else ""
	}

# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class SessionDefaultSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.core.doctype.session_default.session_default import SessionDefault
		from dontmanage.types import DF

		session_defaults: DF.Table[SessionDefault]
	# end: auto-generated types
	pass


@dontmanage.whitelist()
def get_session_default_values():
	settings = dontmanage.get_single("Session Default Settings")
	fields = []
	for default_values in settings.session_defaults:
		reference_doctype = dontmanage.scrub(default_values.ref_doctype)
		fields.append(
			{
				"fieldname": reference_doctype,
				"fieldtype": "Link",
				"options": default_values.ref_doctype,
				"label": _("Default {0}").format(_(default_values.ref_doctype)),
				"default": dontmanage.defaults.get_user_default(reference_doctype),
			}
		)
	return json.dumps(fields)


@dontmanage.whitelist()
def set_session_default_values(default_values):
	default_values = dontmanage.parse_json(default_values)
	for entry in default_values:
		try:
			dontmanage.defaults.set_user_default(entry, default_values.get(entry))
		except Exception:
			return
	return "success"


# called on hook 'on_logout' to clear defaults for the session
def clear_session_defaults():
	settings = dontmanage.get_single("Session Default Settings").session_defaults
	for entry in settings:
		dontmanage.defaults.clear_user_default(dontmanage.scrub(entry.ref_doctype))

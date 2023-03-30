# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.utils import strip_html_tags

no_cache = 1


def get_context(context):
	message_context = dontmanage._dict()
	if hasattr(dontmanage.local, "message"):
		message_context["header"] = dontmanage.local.message_title
		message_context["title"] = strip_html_tags(dontmanage.local.message_title)
		message_context["message"] = dontmanage.local.message
		if hasattr(dontmanage.local, "message_success"):
			message_context["success"] = dontmanage.local.message_success

	elif dontmanage.local.form_dict.id:
		message_id = dontmanage.local.form_dict.id
		key = f"message_id:{message_id}"
		message = dontmanage.cache().get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				dontmanage.local.response["http_status_code"] = message["http_status_code"]

	if not message_context.title:
		message_context.title = dontmanage.form_dict.title

	if not message_context.message:
		message_context.message = dontmanage.form_dict.message

	return message_context

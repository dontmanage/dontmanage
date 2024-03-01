# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

"""Allow adding of likes to documents"""

import json

import dontmanage
from dontmanage import _
from dontmanage.database.schema import add_column
from dontmanage.desk.form.document_follow import follow_document
from dontmanage.utils import get_link_to_form


@dontmanage.whitelist()
def toggle_like(doctype, name, add=False):
	"""Adds / removes the current user in the `__liked_by` property of the given document.
	If column does not exist, will add it in the database.

	The `_liked_by` property is always set from this function and is ignored if set via
	Document API

	:param doctype: DocType of the document to like
	:param name: Name of the document to like
	:param add: `Yes` if like is to be added. If not `Yes` the like will be removed."""

	_toggle_like(doctype, name, add)


def _toggle_like(doctype, name, add, user=None):
	"""Same as toggle_like but hides param `user` from API"""

	if not user:
		user = dontmanage.session.user

	try:
		liked_by = dontmanage.db.get_value(doctype, name, "_liked_by")

		if liked_by:
			liked_by = json.loads(liked_by)
		else:
			liked_by = []

		if add == "Yes":
			if user not in liked_by:
				liked_by.append(user)
				add_comment(doctype, name)
				if dontmanage.get_cached_value("User", user, "follow_liked_documents"):
					follow_document(doctype, name, user)
		else:
			if user in liked_by:
				liked_by.remove(user)
				remove_like(doctype, name)

		if dontmanage.get_meta(doctype).issingle:
			dontmanage.db.set_single_value(doctype, "_liked_by", json.dumps(liked_by), update_modified=False)
		else:
			dontmanage.db.set_value(doctype, name, "_liked_by", json.dumps(liked_by), update_modified=False)

	except dontmanage.db.ProgrammingError as e:
		if dontmanage.db.is_column_missing(e):
			add_column(doctype, "_liked_by", "Text")
			_toggle_like(doctype, name, add, user)
		else:
			raise


def remove_like(doctype, name):
	"""Remove previous Like"""
	# remove Comment
	dontmanage.delete_doc(
		"Comment",
		[
			c.name
			for c in dontmanage.get_all(
				"Comment",
				filters={
					"comment_type": "Like",
					"reference_doctype": doctype,
					"reference_name": name,
					"owner": dontmanage.session.user,
				},
			)
		],
		ignore_permissions=True,
	)


def add_comment(doctype, name):
	doc = dontmanage.get_doc(doctype, name)
	doc.add_comment("Like", _("Liked"))

# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

"""assign/unassign to ToDo"""

import json

import dontmanage
import dontmanage.share
import dontmanage.utils
from dontmanage import _
from dontmanage.desk.doctype.notification_log.notification_log import (
	enqueue_create_notification,
	get_title,
	get_title_html,
)
from dontmanage.desk.form.document_follow import follow_document


class DuplicateToDoError(dontmanage.ValidationError):
	pass


def get(args=None):
	"""get assigned to"""
	if not args:
		args = dontmanage.local.form_dict

	return dontmanage.get_all(
		"ToDo",
		fields=["allocated_to as owner", "name"],
		filters={
			"reference_type": args.get("doctype"),
			"reference_name": args.get("name"),
			"status": ("!=", "Cancelled"),
		},
		limit=5,
	)


@dontmanage.whitelist()
def add(args=None):
	"""add in someone's to do list
	args = {
	        "assign_to": [],
	        "doctype": ,
	        "name": ,
	        "description": ,
	        "assignment_rule":
	}

	"""
	if not args:
		args = dontmanage.local.form_dict

	users_with_duplicate_todo = []
	shared_with_users = []

	for assign_to in dontmanage.parse_json(args.get("assign_to")):
		filters = {
			"reference_type": args["doctype"],
			"reference_name": args["name"],
			"status": "Open",
			"allocated_to": assign_to,
		}

		if dontmanage.get_all("ToDo", filters=filters):
			users_with_duplicate_todo.append(assign_to)
		else:
			from dontmanage.utils import nowdate

			if not args.get("description"):
				args["description"] = _("Assignment for {0} {1}").format(args["doctype"], args["name"])

			d = dontmanage.get_doc(
				{
					"doctype": "ToDo",
					"allocated_to": assign_to,
					"reference_type": args["doctype"],
					"reference_name": args["name"],
					"description": args.get("description"),
					"priority": args.get("priority", "Medium"),
					"status": "Open",
					"date": args.get("date", nowdate()),
					"assigned_by": args.get("assigned_by", dontmanage.session.user),
					"assignment_rule": args.get("assignment_rule"),
				}
			).insert(ignore_permissions=True)

			# set assigned_to if field exists
			if dontmanage.get_meta(args["doctype"]).get_field("assigned_to"):
				dontmanage.db.set_value(args["doctype"], args["name"], "assigned_to", assign_to)

			doc = dontmanage.get_doc(args["doctype"], args["name"])

			# if assignee does not have permissions, share
			if not dontmanage.has_permission(doc=doc, user=assign_to):
				dontmanage.share.add(doc.doctype, doc.name, assign_to)
				shared_with_users.append(assign_to)

			# make this document followed by assigned user
			if dontmanage.get_cached_value("User", assign_to, "follow_assigned_documents"):
				follow_document(args["doctype"], args["name"], assign_to)

			# notify
			notify_assignment(
				d.assigned_by,
				d.allocated_to,
				d.reference_type,
				d.reference_name,
				action="ASSIGN",
				description=args.get("description"),
			)

	if shared_with_users:
		user_list = format_message_for_assign_to(shared_with_users)
		dontmanage.msgprint(
			_("Shared with the following Users with Read access:{0}").format(user_list, alert=True)
		)

	if users_with_duplicate_todo:
		user_list = format_message_for_assign_to(users_with_duplicate_todo)
		dontmanage.msgprint(_("Already in the following Users ToDo list:{0}").format(user_list, alert=True))

	return get(args)


@dontmanage.whitelist()
def add_multiple(args=None):
	if not args:
		args = dontmanage.local.form_dict

	docname_list = json.loads(args["name"])

	for docname in docname_list:
		args.update({"name": docname})
		add(args)


def close_all_assignments(doctype, name):
	assignments = dontmanage.get_all(
		"ToDo",
		fields=["allocated_to"],
		filters=dict(reference_type=doctype, reference_name=name, status=("!=", "Cancelled")),
	)
	if not assignments:
		return False

	for assign_to in assignments:
		set_status(doctype, name, assign_to.allocated_to, status="Closed")

	return True


@dontmanage.whitelist()
def remove(doctype, name, assign_to):
	return set_status(doctype, name, assign_to, status="Cancelled")


def set_status(doctype, name, assign_to, status="Cancelled"):
	"""remove from todo"""
	try:
		todo = dontmanage.db.get_value(
			"ToDo",
			{
				"reference_type": doctype,
				"reference_name": name,
				"allocated_to": assign_to,
				"status": ("!=", status),
			},
		)
		if todo:
			todo = dontmanage.get_doc("ToDo", todo)
			todo.status = status
			todo.save(ignore_permissions=True)

			notify_assignment(todo.assigned_by, todo.allocated_to, todo.reference_type, todo.reference_name)
	except dontmanage.DoesNotExistError:
		pass

	# clear assigned_to if field exists
	if dontmanage.get_meta(doctype).get_field("assigned_to") and status == "Cancelled":
		dontmanage.db.set_value(doctype, name, "assigned_to", None)

	return get({"doctype": doctype, "name": name})


def clear(doctype, name):
	"""
	Clears assignments, return False if not assigned.
	"""
	assignments = dontmanage.get_all(
		"ToDo", fields=["allocated_to"], filters=dict(reference_type=doctype, reference_name=name)
	)
	if not assignments:
		return False

	for assign_to in assignments:
		set_status(doctype, name, assign_to.allocated_to, "Cancelled")

	return True


def notify_assignment(
	assigned_by, allocated_to, doc_type, doc_name, action="CLOSE", description=None
):
	"""
	Notify assignee that there is a change in assignment
	"""
	if not (assigned_by and allocated_to and doc_type and doc_name):
		return

	# return if self assigned or user disabled
	if assigned_by == allocated_to or not dontmanage.db.get_value("User", allocated_to, "enabled"):
		return

	# Search for email address in description -- i.e. assignee
	user_name = dontmanage.get_cached_value("User", dontmanage.session.user, "full_name")
	title = get_title(doc_type, doc_name)
	description_html = f"<div>{description}</div>" if description else None

	if action == "CLOSE":
		subject = _("Your assignment on {0} {1} has been removed by {2}").format(
			dontmanage.bold(doc_type), get_title_html(title), dontmanage.bold(user_name)
		)
	else:
		user_name = dontmanage.bold(user_name)
		document_type = dontmanage.bold(doc_type)
		title = get_title_html(title)
		subject = _("{0} assigned a new task {1} {2} to you").format(user_name, document_type, title)

	notification_doc = {
		"type": "Assignment",
		"document_type": doc_type,
		"subject": subject,
		"document_name": doc_name,
		"from_user": dontmanage.session.user,
		"email_content": description_html,
	}

	enqueue_create_notification(allocated_to, notification_doc)


def format_message_for_assign_to(users):
	return "<br><br>" + "<br>".join(users)

# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json

from bs4 import BeautifulSoup

import dontmanage
from dontmanage import _
from dontmanage.desk.doctype.notification_log.notification_log import (
	enqueue_create_notification,
	get_title,
	get_title_html,
)
from dontmanage.desk.doctype.notification_settings.notification_settings import (
	get_subscribed_documents,
)
from dontmanage.utils import get_fullname


@dontmanage.whitelist()
@dontmanage.read_only()
def get_notifications():
	out = {
		"open_count_doctype": {},
		"targets": {},
	}
	if dontmanage.flags.in_install or not dontmanage.db.get_single_value("System Settings", "setup_complete"):
		return out

	config = get_notification_config()

	if not config:
		return out

	groups = list(config.get("for_doctype")) + list(config.get("for_module"))
	cache = dontmanage.cache()

	notification_count = {}
	notification_percent = {}

	for name in groups:
		count = cache.hget("notification_count:" + name, dontmanage.session.user)
		if count is not None:
			notification_count[name] = count

	out["open_count_doctype"] = get_notifications_for_doctypes(config, notification_count)
	out["targets"] = get_notifications_for_targets(config, notification_percent)

	return out


def get_notifications_for_doctypes(config, notification_count):
	"""Notifications for DocTypes"""
	can_read = dontmanage.get_user().get_can_read()
	open_count_doctype = {}

	for d in config.for_doctype:
		if d in can_read:
			condition = config.for_doctype[d]

			if d in notification_count:
				open_count_doctype[d] = notification_count[d]
			else:
				try:
					if isinstance(condition, dict):
						result = dontmanage.get_list(
							d, fields=["count(*) as count"], filters=condition, ignore_ifnull=True
						)[0].count
					else:
						result = dontmanage.get_attr(condition)()

				except dontmanage.PermissionError:
					dontmanage.clear_messages()
					pass
					# dontmanage.msgprint("Permission Error in notifications for {0}".format(d))

				except Exception as e:
					# OperationalError: (1412, 'Table definition has changed, please retry transaction')
					# InternalError: (1684, 'Table definition is being modified by concurrent DDL statement')
					if e.args and e.args[0] not in (1412, 1684):
						raise

				else:
					open_count_doctype[d] = result
					dontmanage.cache().hset("notification_count:" + d, dontmanage.session.user, result)

	return open_count_doctype


def get_notifications_for_targets(config, notification_percent):
	"""Notifications for doc targets"""
	can_read = dontmanage.get_user().get_can_read()
	doc_target_percents = {}

	# doc_target_percents = {
	# 	"Company": {
	# 		"Acme": 87,
	# 		"RobotsRUs": 50,
	# 	}, {}...
	# }

	for doctype in config.targets:
		if doctype in can_read:
			if doctype in notification_percent:
				doc_target_percents[doctype] = notification_percent[doctype]
			else:
				doc_target_percents[doctype] = {}
				d = config.targets[doctype]
				condition = d["filters"]
				target_field = d["target_field"]
				value_field = d["value_field"]
				try:
					if isinstance(condition, dict):
						doc_list = dontmanage.get_list(
							doctype,
							fields=["name", target_field, value_field],
							filters=condition,
							limit_page_length=100,
							ignore_ifnull=True,
						)

				except dontmanage.PermissionError:
					dontmanage.clear_messages()
					pass
				except Exception as e:
					if e.args[0] not in (1412, 1684):
						raise

				else:
					for doc in doc_list:
						value = doc[value_field]
						target = doc[target_field]
						doc_target_percents[doctype][doc.name] = (value / target * 100) if value < target else 100

	return doc_target_percents


def clear_notifications(user=None):
	if dontmanage.flags.in_install:
		return
	cache = dontmanage.cache()
	config = get_notification_config()

	if not config:
		return

	for_doctype = list(config.get("for_doctype")) if config.get("for_doctype") else []
	for_module = list(config.get("for_module")) if config.get("for_module") else []
	groups = for_doctype + for_module

	for name in groups:
		if user:
			cache.hdel("notification_count:" + name, user)
		else:
			cache.delete_key("notification_count:" + name)


def clear_notification_config(user):
	dontmanage.cache().hdel("notification_config", user)


def delete_notification_count_for(doctype):
	dontmanage.cache().delete_key("notification_count:" + doctype)


def clear_doctype_notifications(doc, method=None, *args, **kwargs):
	config = get_notification_config()
	if not config:
		return
	if isinstance(doc, str):
		doctype = doc  # assuming doctype name was passed directly
	else:
		doctype = doc.doctype

	if doctype in config.for_doctype:
		delete_notification_count_for(doctype)
		return


@dontmanage.whitelist()
def get_notification_info():
	config = get_notification_config()
	out = get_notifications()
	can_read = dontmanage.get_user().get_can_read()
	conditions = {}
	module_doctypes = {}
	doctype_info = dict(dontmanage.db.sql("""select name, module from tabDocType"""))

	for d in list(set(can_read + list(config.for_doctype))):
		if d in config.for_doctype:
			conditions[d] = config.for_doctype[d]

		if d in doctype_info:
			module_doctypes.setdefault(doctype_info[d], []).append(d)

	out.update(
		{
			"conditions": conditions,
			"module_doctypes": module_doctypes,
		}
	)

	return out


def get_notification_config():
	user = dontmanage.session.user or "Guest"

	def _get():
		subscribed_documents = get_subscribed_documents()
		config = dontmanage._dict()
		hooks = dontmanage.get_hooks()
		if hooks:
			for notification_config in hooks.notification_config:
				nc = dontmanage.get_attr(notification_config)()
				for key in ("for_doctype", "for_module", "for_other", "targets"):
					config.setdefault(key, {})
					if key == "for_doctype":
						if len(subscribed_documents) > 0:
							key_config = nc.get(key, {})
							subscribed_docs_config = dontmanage._dict()
							for document in subscribed_documents:
								if key_config.get(document):
									subscribed_docs_config[document] = key_config.get(document)
							config[key].update(subscribed_docs_config)
						else:
							config[key].update(nc.get(key, {}))
					else:
						config[key].update(nc.get(key, {}))
		return config

	return dontmanage.cache().hget("notification_config", user, _get)


def get_filters_for(doctype):
	"""get open filters for doctype"""
	config = get_notification_config()
	doctype_config = config.get("for_doctype").get(doctype, {})
	filters = doctype_config if not isinstance(doctype_config, str) else None

	return filters


@dontmanage.whitelist()
@dontmanage.read_only()
def get_open_count(doctype, name, items=None):
	"""Get open count for given transactions and filters

	:param doctype: Reference DocType
	:param name: Reference Name
	:param transactions: List of transactions (json/dict)
	:param filters: optional filters (json/list)"""

	if dontmanage.flags.in_migrate or dontmanage.flags.in_install:
		return {"count": []}

	doc = dontmanage.get_doc(doctype, name)
	doc.check_permission()
	meta = doc.meta
	links = meta.get_dashboard_data()

	# compile all items in a list
	if items is None:
		items = []
		for group in links.transactions:
			items.extend(group.get("items"))

	if not isinstance(items, list):
		items = json.loads(items)

	out = []
	for d in items:
		if d in links.get("internal_links", {}):
			continue

		filters = get_filters_for(d)
		fieldname = links.get("non_standard_fieldnames", {}).get(d, links.get("fieldname"))
		data = {"name": d}
		if filters:
			# get the fieldname for the current document
			# we only need open documents related to the current document
			filters[fieldname] = name
			total = len(
				dontmanage.get_all(d, fields="name", filters=filters, limit=100, distinct=True, ignore_ifnull=True)
			)
			data["open_count"] = total

		total = len(
			dontmanage.get_all(
				d, fields="name", filters={fieldname: name}, limit=100, distinct=True, ignore_ifnull=True
			)
		)
		data["count"] = total
		out.append(data)

	out = {
		"count": out,
	}

	if not meta.custom:
		module = dontmanage.get_meta_module(doctype)
		if hasattr(module, "get_timeline_data"):
			out["timeline_data"] = module.get_timeline_data(doctype, name)

	return out


def notify_mentions(ref_doctype, ref_name, content):
	if ref_doctype and ref_name and content:
		mentions = extract_mentions(content)

		if not mentions:
			return

		sender_fullname = get_fullname(dontmanage.session.user)
		title = get_title(ref_doctype, ref_name)

		recipients = [
			dontmanage.db.get_value(
				"User",
				{"enabled": 1, "name": name, "user_type": "System User", "allowed_in_mentions": 1},
				"email",
			)
			for name in mentions
		]

		notification_message = _("""{0} mentioned you in a comment in {1} {2}""").format(
			dontmanage.bold(sender_fullname), dontmanage.bold(ref_doctype), get_title_html(title)
		)

		notification_doc = {
			"type": "Mention",
			"document_type": ref_doctype,
			"document_name": ref_name,
			"subject": notification_message,
			"from_user": dontmanage.session.user,
			"email_content": content,
		}

		enqueue_create_notification(recipients, notification_doc)


def extract_mentions(txt):
	"""Find all instances of @mentions in the html."""
	soup = BeautifulSoup(txt, "html.parser")
	emails = []
	for mention in soup.find_all(class_="mention"):
		if mention.get("data-is-group") == "true":
			try:
				user_group = dontmanage.get_cached_doc("User Group", mention["data-id"])
				emails += [d.user for d in user_group.user_group_members]
			except dontmanage.DoesNotExistError:
				pass
			continue
		email = mention["data-id"]
		emails.append(email)

	return emails

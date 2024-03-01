# Copyright (c) 2017, DontManage Technologies and contributors
# License: MIT. See LICENSE

import base64
import hashlib
import hmac
import json
from time import sleep
from urllib.parse import urlparse

import requests

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.utils.background_jobs import get_queues_timeout
from dontmanage.utils.jinja import validate_template
from dontmanage.utils.safe_exec import get_safe_globals

WEBHOOK_SECRET_HEADER = "X-DontManage-Webhook-Signature"


class Webhook(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.integrations.doctype.webhook_data.webhook_data import WebhookData
		from dontmanage.integrations.doctype.webhook_header.webhook_header import WebhookHeader
		from dontmanage.types import DF

		background_jobs_queue: DF.Autocomplete | None
		condition: DF.SmallText | None
		enable_security: DF.Check
		enabled: DF.Check
		is_dynamic_url: DF.Check
		meets_condition: DF.Data | None
		preview_document: DF.DynamicLink | None
		preview_request_body: DF.Code | None
		request_method: DF.Literal["POST", "PUT", "DELETE"]
		request_structure: DF.Literal["", "Form URL-Encoded", "JSON"]
		request_url: DF.SmallText
		timeout: DF.Int
		webhook_data: DF.Table[WebhookData]
		webhook_docevent: DF.Literal[
			"after_insert",
			"on_update",
			"on_submit",
			"on_cancel",
			"on_trash",
			"on_update_after_submit",
			"on_change",
		]
		webhook_doctype: DF.Link
		webhook_headers: DF.Table[WebhookHeader]
		webhook_json: DF.Code | None
		webhook_secret: DF.Password | None
	# end: auto-generated types

	def validate(self):
		self.validate_docevent()
		self.validate_condition()
		self.validate_request_url()
		self.validate_request_body()
		self.validate_repeating_fields()
		self.validate_secret()
		self.preview_document = None

	def on_update(self):
		dontmanage.cache.delete_value("webhooks")

	def validate_docevent(self):
		if self.webhook_doctype:
			is_submittable = dontmanage.get_value("DocType", self.webhook_doctype, "is_submittable")
			if not is_submittable and self.webhook_docevent in [
				"on_submit",
				"on_cancel",
				"on_update_after_submit",
			]:
				dontmanage.throw(_("DocType must be Submittable for the selected Doc Event"))

	def validate_condition(self):
		temp_doc = dontmanage.new_doc(self.webhook_doctype)
		if self.condition:
			try:
				dontmanage.safe_eval(self.condition, eval_locals=get_context(temp_doc))
			except Exception as e:
				dontmanage.throw(_("Invalid Condition: {}").format(e))

	def validate_request_url(self):
		try:
			request_url = urlparse(self.request_url).netloc
			if not request_url:
				raise dontmanage.ValidationError
		except Exception as e:
			dontmanage.throw(_("Check Request URL"), exc=e)

	def validate_request_body(self):
		if self.request_structure:
			if self.request_structure == "Form URL-Encoded":
				self.webhook_json = None
			elif self.request_structure == "JSON":
				validate_template(self.webhook_json)
				self.webhook_data = []

	def validate_repeating_fields(self):
		"""Error when Same Field is entered multiple times in webhook_data"""
		webhook_data = [entry.fieldname for entry in self.webhook_data]
		if len(webhook_data) != len(set(webhook_data)):
			dontmanage.throw(_("Same Field is entered more than once"))

	def validate_secret(self):
		if self.enable_security:
			try:
				self.get_password("webhook_secret", False).encode("utf8")
			except Exception:
				dontmanage.throw(_("Invalid Webhook Secret"))

	@dontmanage.whitelist()
	def generate_preview(self):
		# This function doesn't need to do anything specific as virtual fields
		# get evaluated automatically.
		pass

	@property
	def meets_condition(self):
		if not self.condition:
			return _("Yes")

		if not (self.preview_document and self.webhook_doctype):
			return _("Select a document to check if it meets conditions.")

		try:
			doc = dontmanage.get_cached_doc(self.webhook_doctype, self.preview_document)
			met_condition = dontmanage.safe_eval(self.condition, eval_locals=get_context(doc))
		except Exception as e:
			return _("Failed to evaluate conditions: {}").format(e)
		return _("Yes") if met_condition else _("No")

	@property
	def preview_request_body(self):
		if not (self.preview_document and self.webhook_doctype):
			return _("Select a document to preview request data")

		try:
			doc = dontmanage.get_cached_doc(self.webhook_doctype, self.preview_document)
			return dontmanage.as_json(get_webhook_data(doc, self))
		except Exception as e:
			return _("Failed to compute request body: {}").format(e)


def get_context(doc):
	return {"doc": doc, "utils": get_safe_globals().get("dontmanage").get("utils")}


def enqueue_webhook(doc, webhook) -> None:
	request_url = headers = data = None
	try:
		webhook: Webhook = dontmanage.get_doc("Webhook", webhook.get("name"))
		request_url = webhook.request_url
		if webhook.is_dynamic_url:
			request_url = dontmanage.render_template(webhook.request_url, get_context(doc))
		headers = get_webhook_headers(doc, webhook)
		data = get_webhook_data(doc, webhook)

	except Exception as e:
		dontmanage.logger().debug({"enqueue_webhook_error": e})
		log_request(webhook.name, doc.name, request_url, headers, data)
		return

	for i in range(3):
		try:
			r = requests.request(
				method=webhook.request_method,
				url=request_url,
				data=json.dumps(data, default=str),
				headers=headers,
				timeout=webhook.timeout or 5,
			)
			r.raise_for_status()
			dontmanage.logger().debug({"webhook_success": r.text})
			log_request(webhook.name, doc.name, request_url, headers, data, r)
			break

		except requests.exceptions.ReadTimeout as e:
			dontmanage.logger().debug({"webhook_error": e, "try": i + 1})
			log_request(webhook.name, doc.name, request_url, headers, data)

		except Exception as e:
			dontmanage.logger().debug({"webhook_error": e, "try": i + 1})
			log_request(webhook.name, doc.name, request_url, headers, data, r)
			sleep(3 * i + 1)
			if i != 2:
				continue


def log_request(
	webhook: str,
	docname: str,
	url: str,
	headers: dict,
	data: dict,
	res: requests.Response | None = None,
):
	request_log = dontmanage.get_doc(
		{
			"doctype": "Webhook Request Log",
			"webhook": webhook,
			"reference_document": docname,
			"user": dontmanage.session.user if dontmanage.session.user else None,
			"url": url,
			"headers": dontmanage.as_json(headers) if headers else None,
			"data": dontmanage.as_json(data) if data else None,
			"response": res and res.text,
			"error": dontmanage.get_traceback(),
		}
	)

	request_log.save(ignore_permissions=True)


def get_webhook_headers(doc, webhook):
	headers = {}

	if webhook.enable_security:
		data = get_webhook_data(doc, webhook)
		signature = base64.b64encode(
			hmac.new(
				webhook.get_password("webhook_secret").encode("utf8"),
				json.dumps(data).encode("utf8"),
				hashlib.sha256,
			).digest()
		)
		headers[WEBHOOK_SECRET_HEADER] = signature

	if webhook.webhook_headers:
		for h in webhook.webhook_headers:
			if h.get("key") and h.get("value"):
				headers[h.get("key")] = h.get("value")

	return headers


def get_webhook_data(doc, webhook):
	data = {}
	doc = doc.as_dict(convert_dates_to_str=True)

	if webhook.webhook_data:
		data = {w.key: doc.get(w.fieldname) for w in webhook.webhook_data}
	elif webhook.webhook_json:
		data = dontmanage.render_template(webhook.webhook_json, get_context(doc))
		data = json.loads(data)

	return data


@dontmanage.whitelist()
def get_all_queues():
	"""Fetches all workers and returns a list of available queue names."""
	dontmanage.only_for("System Manager")

	return get_queues_timeout().keys()

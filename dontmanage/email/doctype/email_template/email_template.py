# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage.model.document import Document
from dontmanage.utils.jinja import validate_template


class EmailTemplate(Document):
	def validate(self):
		if self.use_html:
			validate_template(self.response_html)
		else:
			validate_template(self.response)

	def get_formatted_subject(self, doc):
		return dontmanage.render_template(self.subject, doc)

	def get_formatted_response(self, doc):
		if self.use_html:
			return dontmanage.render_template(self.response_html, doc)

		return dontmanage.render_template(self.response, doc)

	def get_formatted_email(self, doc):
		if isinstance(doc, str):
			doc = json.loads(doc)

		return {"subject": self.get_formatted_subject(doc), "message": self.get_formatted_response(doc)}


@dontmanage.whitelist()
def get_email_template(template_name, doc):
	"""Returns the processed HTML of a email template with the given doc"""
	if isinstance(doc, str):
		doc = json.loads(doc)

	email_template = dontmanage.get_doc("Email Template", template_name)
	return email_template.get_formatted_email(doc)

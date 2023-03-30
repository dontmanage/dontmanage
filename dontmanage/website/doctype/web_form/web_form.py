# Copyright (c) 2015, DontManage and contributors
# License: MIT. See LICENSE

import json
import os

import dontmanage
from dontmanage import _, scrub
from dontmanage.core.api.file import get_max_file_size
from dontmanage.core.doctype.file import remove_file_by_url
from dontmanage.desk.form.meta import get_code_files_via_hooks
from dontmanage.modules.utils import export_module_json, get_doc_module
from dontmanage.rate_limiter import rate_limit
from dontmanage.utils import cstr, dict_with_keys, strip_html
from dontmanage.website.utils import get_boot_data, get_comment_list, get_sidebar_items
from dontmanage.website.website_generator import WebsiteGenerator


class WebForm(WebsiteGenerator):
	website = dontmanage._dict(no_cache=1)

	def onload(self):
		super().onload()

	def validate(self):
		super().validate()

		if not self.module:
			self.module = dontmanage.db.get_value("DocType", self.doc_type, "module")

		in_user_env = not (
			dontmanage.flags.in_install
			or dontmanage.flags.in_patch
			or dontmanage.flags.in_test
			or dontmanage.flags.in_fixtures
		)
		if in_user_env and self.is_standard and not dontmanage.conf.developer_mode:
			# only published can be changed for standard web forms
			if self.has_value_changed("published"):
				published_value = self.published
				self.reload()
				self.published = published_value
			else:
				dontmanage.throw(_("You need to be in developer mode to edit a Standard Web Form"))

		if not dontmanage.flags.in_import:
			self.validate_fields()

	def validate_fields(self):
		"""Validate all fields are present"""
		from dontmanage.model import no_value_fields

		missing = []
		meta = dontmanage.get_meta(self.doc_type)
		for df in self.web_form_fields:
			if df.fieldname and (df.fieldtype not in no_value_fields and not meta.has_field(df.fieldname)):
				missing.append(df.fieldname)

		if missing:
			dontmanage.throw(_("Following fields are missing:") + "<br>" + "<br>".join(missing))

	def reset_field_parent(self):
		"""Convert link fields to select with names as options"""
		for df in self.web_form_fields:
			df.parent = self.doc_type

	# export
	def on_update(self):
		"""
		Writes the .txt for this page and if write_content is checked,
		it will write out a .html file
		"""
		path = export_module_json(self, self.is_standard, self.module)

		if path:
			# js
			if not os.path.exists(path + ".js"):
				with open(path + ".js", "w") as f:
					f.write(
						"""dontmanage.ready(function() {
	// bind events here
})"""
					)

			# py
			if not os.path.exists(path + ".py"):
				with open(path + ".py", "w") as f:
					f.write(
						"""import dontmanage

def get_context(context):
	# do your magic here
	pass
"""
					)

	def get_context(self, context):
		"""Build context to render the `web_form.html` template"""
		context.in_edit_mode = False
		context.in_view_mode = False

		if dontmanage.form_dict.is_list:
			context.template = "website/doctype/web_form/templates/web_list.html"
		else:
			context.template = "website/doctype/web_form/templates/web_form.html"

		# check permissions
		if dontmanage.form_dict.name:
			if dontmanage.session.user == "Guest":
				dontmanage.throw(
					_("You need to be logged in to access this {0}.").format(self.doc_type),
					dontmanage.PermissionError,
				)

			if not dontmanage.db.exists(self.doc_type, dontmanage.form_dict.name):
				raise dontmanage.PageDoesNotExistError()

			if not self.has_web_form_permission(self.doc_type, dontmanage.form_dict.name):
				dontmanage.throw(
					_("You don't have the permissions to access this document"), dontmanage.PermissionError
				)

		if dontmanage.local.path == self.route:
			path = f"/{self.route}/list" if self.show_list else f"/{self.route}/new"
			dontmanage.redirect(path)

		if dontmanage.form_dict.is_list and not self.show_list:
			dontmanage.redirect(f"/{self.route}/new")

		if dontmanage.form_dict.is_edit and not self.allow_edit:
			context.in_view_mode = True
			dontmanage.redirect(f"/{self.route}/{dontmanage.form_dict.name}")

		if dontmanage.form_dict.is_edit:
			context.in_edit_mode = True

		if dontmanage.form_dict.is_read:
			context.in_view_mode = True

		if (
			not dontmanage.form_dict.is_edit
			and not dontmanage.form_dict.is_read
			and self.allow_edit
			and dontmanage.form_dict.name
		):
			context.in_edit_mode = True
			dontmanage.redirect(f"/{dontmanage.local.path}/edit")

		if (
			dontmanage.session.user != "Guest"
			and self.login_required
			and not self.allow_multiple
			and not dontmanage.form_dict.name
			and not dontmanage.form_dict.is_list
		):
			name = dontmanage.db.get_value(self.doc_type, {"owner": dontmanage.session.user}, "name")
			if name:
				context.in_view_mode = True
				dontmanage.redirect(f"/{self.route}/{name}")

		# Show new form when
		# - User is Guest
		# - Login not required
		route_to_new = dontmanage.session.user == "Guest" or not self.login_required
		if not dontmanage.form_dict.is_new and route_to_new:
			dontmanage.redirect(f"/{self.route}/new")

		self.reset_field_parent()

		# add keys from form_dict to context
		context.update(dict_with_keys(dontmanage.form_dict, ["is_list", "is_new", "is_edit", "is_read"]))

		for df in self.web_form_fields:
			if df.fieldtype == "Column Break":
				context.has_column_break = True
				break

		# load web form doc
		context.web_form_doc = self.as_dict(no_nulls=True)
		context.web_form_doc.update(
			dict_with_keys(context, ["is_list", "is_new", "in_edit_mode", "in_view_mode"])
		)

		if self.show_sidebar and self.website_sidebar:
			context.sidebar_items = get_sidebar_items(self.website_sidebar)

		if dontmanage.form_dict.is_list:
			self.load_list_data(context)
		else:
			self.load_form_data(context)

		self.add_custom_context_and_script(context)
		self.load_translations(context)
		self.add_metatags(context)

		context.boot = get_boot_data()
		context.boot["link_title_doctypes"] = dontmanage.boot.get_link_title_doctypes()

	def add_metatags(self, context):
		description = self.meta_description

		if not description and self.introduction_text:
			description = self.introduction_text[:140]

		context.metatags = {
			"name": self.meta_title or self.title,
			"description": description,
			"image": self.meta_image,
		}

	def load_translations(self, context):
		translated_messages = dontmanage.translate.get_dict("doctype", self.doc_type)
		# Sr is not added by default, had to be added manually
		translated_messages["Sr"] = _("Sr")
		context.translated_messages = dontmanage.as_json(translated_messages)

	def load_list_data(self, context):
		if not self.list_columns:
			self.list_columns = get_in_list_view_fields(self.doc_type)
			context.web_form_doc.list_columns = self.list_columns

	def load_form_data(self, context):
		"""Load document `doc` and `layout` properties for template"""
		context.parents = []
		if self.show_list:
			context.parents.append(
				{
					"label": _(self.title),
					"route": f"{self.route}/list",
				}
			)

		context.parents = self.get_parents(context)

		if self.breadcrumbs:
			context.parents = dontmanage.safe_eval(self.breadcrumbs, {"_": _})

		if self.show_list and dontmanage.form_dict.is_new:
			context.title = _("New {0}").format(context.title)

		context.has_header = (dontmanage.form_dict.name or dontmanage.form_dict.is_new) and (
			dontmanage.session.user != "Guest" or not self.login_required
		)

		if context.success_message:
			context.success_message = dontmanage.db.escape(context.success_message.replace("\n", "<br>")).strip(
				"'"
			)

		if not context.max_attachment_size:
			context.max_attachment_size = get_max_file_size() / 1024 / 1024

		# For Table fields, server-side processing for meta
		for field in context.web_form_doc.web_form_fields:
			if field.fieldtype == "Table":
				field.fields = get_in_list_view_fields(field.options)

			if field.fieldtype == "Link":
				field.fieldtype = "Autocomplete"
				field.options = get_link_options(
					self.name, field.options, field.allow_read_on_all_link_options
				)

		context.reference_doc = {}

		# load reference doc
		if dontmanage.form_dict.name:
			context.doc_name = dontmanage.form_dict.name
			context.reference_doc = dontmanage.get_doc(self.doc_type, context.doc_name)
			context.web_form_title = context.title
			context.title = (
				strip_html(context.reference_doc.get(context.reference_doc.meta.get_title_field()))
				or context.doc_name
			)
			context.reference_doc.add_seen()
			context.reference_doctype = context.reference_doc.doctype
			context.reference_name = context.reference_doc.name

			if self.show_attachments:
				context.attachments = dontmanage.get_all(
					"File",
					filters={
						"attached_to_name": context.reference_name,
						"attached_to_doctype": context.reference_doctype,
						"is_private": 0,
					},
					fields=["file_name", "file_url", "file_size"],
				)

			if self.allow_comments:
				context.comment_list = get_comment_list(
					context.reference_doc.doctype, context.reference_doc.name
				)

			context.reference_doc = context.reference_doc.as_dict(no_nulls=True)

	def add_custom_context_and_script(self, context):
		"""Update context from module if standard and append script"""
		if self.is_standard:
			web_form_module = get_web_form_module(self)
			new_context = web_form_module.get_context(context)

			if new_context:
				context.update(new_context)

			js_path = os.path.join(os.path.dirname(web_form_module.__file__), scrub(self.name) + ".js")
			if os.path.exists(js_path):
				script = dontmanage.render_template(open(js_path).read(), context)

				for path in get_code_files_via_hooks("webform_include_js", context.doc_type):
					custom_js = dontmanage.render_template(open(path).read(), context)
					script = "\n\n".join([script, custom_js])

				context.script = script

			css_path = os.path.join(os.path.dirname(web_form_module.__file__), scrub(self.name) + ".css")
			if os.path.exists(css_path):
				style = open(css_path).read()

				for path in get_code_files_via_hooks("webform_include_css", context.doc_type):
					custom_css = open(path).read()
					style = "\n\n".join([style, custom_css])

				context.style = style

	def get_parents(self, context):
		parents = None

		if context.is_list and not context.parents:
			parents = [{"title": _("My Account"), "name": "me"}]
		elif context.parents:
			parents = context.parents

		return parents

	def validate_mandatory(self, doc):
		"""Validate mandatory web form fields"""
		missing = []
		for f in self.web_form_fields:
			if f.reqd and doc.get(f.fieldname) in (None, [], ""):
				missing.append(f)

		if missing:
			dontmanage.throw(
				_("Mandatory Information missing:")
				+ "<br><br>"
				+ "<br>".join(f"{d.label} ({d.fieldtype})" for d in missing)
			)

	def allow_website_search_indexing(self):
		return False

	def has_web_form_permission(self, doctype, name, ptype="read"):
		if dontmanage.session.user == "Guest":
			return False

		if self.apply_document_permissions:
			return dontmanage.get_doc(doctype, name).has_permission(permtype=ptype)

		# owner matches
		elif dontmanage.db.get_value(doctype, name, "owner") == dontmanage.session.user:
			return True

		elif dontmanage.has_website_permission(name, ptype=ptype, doctype=doctype):
			return True

		elif check_webform_perm(doctype, name):
			return True

		else:
			return False


def get_web_form_module(doc):
	if doc.is_standard:
		return get_doc_module(doc.module, doc.doctype, doc.name)


@dontmanage.whitelist(allow_guest=True)
@rate_limit(key="web_form", limit=5, seconds=60, methods=["POST"])
def accept(web_form, data):
	"""Save the web form"""
	data = dontmanage._dict(json.loads(data))

	files = []
	files_to_delete = []

	web_form = dontmanage.get_doc("Web Form", web_form)
	doctype = web_form.doc_type

	if data.name and not web_form.allow_edit:
		dontmanage.throw(_("You are not allowed to update this Web Form Document"))

	dontmanage.flags.in_web_form = True
	meta = dontmanage.get_meta(doctype)

	if data.name:
		# update
		doc = dontmanage.get_doc(doctype, data.name)
	else:
		# insert
		doc = dontmanage.new_doc(doctype)

	# set values
	for field in web_form.web_form_fields:
		fieldname = field.fieldname
		df = meta.get_field(fieldname)
		value = data.get(fieldname, "")

		if df and df.fieldtype in ("Attach", "Attach Image"):
			if value and "data:" and "base64" in value:
				files.append((fieldname, value))
				if not doc.name:
					doc.set(fieldname, "")
				continue

			elif not value and doc.get(fieldname):
				files_to_delete.append(doc.get(fieldname))

		doc.set(fieldname, value)

	if doc.name:
		if web_form.has_web_form_permission(doctype, doc.name, "write"):
			doc.save(ignore_permissions=True)
		else:
			# only if permissions are present
			doc.save()

	else:
		# insert
		if web_form.login_required and dontmanage.session.user == "Guest":
			dontmanage.throw(_("You must login to submit this form"))

		ignore_mandatory = True if files else False

		doc.insert(ignore_permissions=True, ignore_mandatory=ignore_mandatory)

	# add files
	if files:
		for f in files:
			fieldname, filedata = f

			# remove earlier attached file (if exists)
			if doc.get(fieldname):
				remove_file_by_url(doc.get(fieldname), doctype=doctype, name=doc.name)

			# save new file
			filename, dataurl = filedata.split(",", 1)
			_file = dontmanage.get_doc(
				{
					"doctype": "File",
					"file_name": filename,
					"attached_to_doctype": doctype,
					"attached_to_name": doc.name,
					"content": dataurl,
					"decode": True,
				}
			)
			_file.save()

			# update values
			doc.set(fieldname, _file.file_url)

		doc.save(ignore_permissions=True)

	if files_to_delete:
		for f in files_to_delete:
			if f:
				remove_file_by_url(f, doctype=doctype, name=doc.name)

	dontmanage.flags.web_form_doc = doc
	return doc


@dontmanage.whitelist()
def delete(web_form_name, docname):
	web_form = dontmanage.get_doc("Web Form", web_form_name)

	owner = dontmanage.db.get_value(web_form.doc_type, docname, "owner")
	if dontmanage.session.user == owner and web_form.allow_delete:
		dontmanage.delete_doc(web_form.doc_type, docname, ignore_permissions=True)
	else:
		raise dontmanage.PermissionError("Not Allowed")


@dontmanage.whitelist()
def delete_multiple(web_form_name, docnames):
	web_form = dontmanage.get_doc("Web Form", web_form_name)

	docnames = json.loads(docnames)

	allowed_docnames = []
	restricted_docnames = []

	for docname in docnames:
		owner = dontmanage.db.get_value(web_form.doc_type, docname, "owner")
		if dontmanage.session.user == owner and web_form.allow_delete:
			allowed_docnames.append(docname)
		else:
			restricted_docnames.append(docname)

	for docname in allowed_docnames:
		dontmanage.delete_doc(web_form.doc_type, docname, ignore_permissions=True)

	if restricted_docnames:
		raise dontmanage.PermissionError(
			"You do not have permisssion to delete " + ", ".join(restricted_docnames)
		)


def check_webform_perm(doctype, name):
	doc = dontmanage.get_doc(doctype, name)
	if hasattr(doc, "has_webform_permission"):
		if doc.has_webform_permission():
			return True


@dontmanage.whitelist(allow_guest=True)
def get_web_form_filters(web_form_name):
	web_form = dontmanage.get_doc("Web Form", web_form_name)
	return [field for field in web_form.web_form_fields if field.show_in_filter]


@dontmanage.whitelist(allow_guest=True)
def get_form_data(doctype, docname=None, web_form_name=None):
	web_form = dontmanage.get_doc("Web Form", web_form_name)

	if web_form.login_required and dontmanage.session.user == "Guest":
		dontmanage.throw(_("Not Permitted"), dontmanage.PermissionError)

	out = dontmanage._dict()
	out.web_form = web_form

	if dontmanage.session.user != "Guest" and not docname and not web_form.allow_multiple:
		docname = dontmanage.db.get_value(doctype, {"owner": dontmanage.session.user}, "name")

	if docname:
		doc = dontmanage.get_doc(doctype, docname)
		if web_form.has_web_form_permission(doctype, docname, ptype="read"):
			out.doc = doc
		else:
			dontmanage.throw(_("Not permitted"), dontmanage.PermissionError)

	# For Table fields, server-side processing for meta
	for field in out.web_form.web_form_fields:
		if field.fieldtype == "Table":
			field.fields = get_in_list_view_fields(field.options)
			out.update({field.fieldname: field.fields})

		if field.fieldtype == "Link":
			field.fieldtype = "Autocomplete"
			field.options = get_link_options(
				web_form_name, field.options, field.allow_read_on_all_link_options
			)

	return out


@dontmanage.whitelist()
def get_in_list_view_fields(doctype):
	meta = dontmanage.get_meta(doctype)
	fields = []

	if meta.title_field:
		fields.append(meta.title_field)
	else:
		fields.append("name")

	if meta.has_field("status"):
		fields.append("status")

	fields += [df.fieldname for df in meta.fields if df.in_list_view and df.fieldname not in fields]

	def get_field_df(fieldname):
		if fieldname == "name":
			return {"label": "Name", "fieldname": "name", "fieldtype": "Data"}
		return meta.get_field(fieldname).as_dict()

	return [get_field_df(f) for f in fields]


@dontmanage.whitelist(allow_guest=True)
def get_link_options(web_form_name, doctype, allow_read_on_all_link_options=False):
	web_form_doc = dontmanage.get_doc("Web Form", web_form_name)
	doctype_validated = False
	limited_to_user = False
	if web_form_doc.login_required:
		# check if dontmanage session user is not guest or admin
		if dontmanage.session.user != "Guest":
			doctype_validated = True

			if not allow_read_on_all_link_options:
				limited_to_user = True
		else:
			dontmanage.throw(_("You must be logged in to use this form."), dontmanage.PermissionError)

	else:
		for field in web_form_doc.web_form_fields:
			if field.options == doctype:
				doctype_validated = True
				break

	if doctype_validated:
		link_options, filters = [], {}

		if limited_to_user:
			filters = {"owner": dontmanage.session.user}

		fields = ["name as value"]

		title_field = dontmanage.db.get_value("DocType", doctype, "title_field", cache=1)
		show_title_field_in_link = (
			dontmanage.db.get_value("DocType", doctype, "show_title_field_in_link", cache=1) == 1
		)
		if title_field and show_title_field_in_link:
			fields.append(f"{title_field} as label")

		link_options = dontmanage.get_all(doctype, filters, fields)

		if title_field and show_title_field_in_link:
			return json.dumps(link_options, default=str)
		else:
			return "\n".join([doc.value for doc in link_options])

	else:
		raise dontmanage.PermissionError(
			_("You don't have permission to access the {0} DocType.").format(doctype)
		)

# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

from jinja2 import TemplateSyntaxError

import dontmanage
from dontmanage import _, throw
from dontmanage.contacts.address_and_contact import set_link_title
from dontmanage.core.doctype.dynamic_link.dynamic_link import deduplicate_dynamic_links
from dontmanage.model.document import Document
from dontmanage.model.naming import make_autoname
from dontmanage.utils import cstr


class Address(Document):
	def __setup__(self):
		self.flags.linked = False

	def autoname(self):
		if not self.address_title:
			if self.links:
				self.address_title = self.links[0].link_name

		if self.address_title:
			self.name = cstr(self.address_title).strip() + "-" + cstr(_(self.address_type)).strip()
			if dontmanage.db.exists("Address", self.name):
				self.name = make_autoname(
					cstr(self.address_title).strip() + "-" + cstr(self.address_type).strip() + "-.#"
				)
		else:
			throw(_("Address Title is mandatory."))

	def validate(self):
		self.link_address()
		self.validate_preferred_address()
		set_link_title(self)
		deduplicate_dynamic_links(self)

	def link_address(self):
		"""Link address based on owner"""
		if not self.links:
			contact_name = dontmanage.db.get_value("Contact", {"email_id": self.owner})
			if contact_name:
				contact = dontmanage.get_cached_doc("Contact", contact_name)
				for link in contact.links:
					self.append("links", dict(link_doctype=link.link_doctype, link_name=link.link_name))
				return True

		return False

	def validate_preferred_address(self):
		preferred_fields = ["is_primary_address", "is_shipping_address"]

		for field in preferred_fields:
			if self.get(field):
				for link in self.links:
					address = get_preferred_address(link.link_doctype, link.link_name, field)

					if address:
						update_preferred_address(address, field)

	def get_display(self):
		return get_address_display(self.as_dict())

	def has_link(self, doctype, name):
		for link in self.links:
			if link.link_doctype == doctype and link.link_name == name:
				return True

	def has_common_link(self, doc):
		reference_links = [(link.link_doctype, link.link_name) for link in doc.links]
		for link in self.links:
			if (link.link_doctype, link.link_name) in reference_links:
				return True

		return False


def get_preferred_address(doctype, name, preferred_key="is_primary_address"):
	if preferred_key in ["is_shipping_address", "is_primary_address"]:
		address = dontmanage.db.sql(
			""" SELECT
				addr.name
			FROM
				`tabAddress` addr, `tabDynamic Link` dl
			WHERE
				dl.parent = addr.name and dl.link_doctype = %s and
				dl.link_name = %s and ifnull(addr.disabled, 0) = 0 and
				%s = %s
			"""
			% ("%s", "%s", preferred_key, "%s"),
			(doctype, name, 1),
			as_dict=1,
		)

		if address:
			return address[0].name

	return


@dontmanage.whitelist()
def get_default_address(doctype, name, sort_key="is_primary_address"):
	"""Returns default Address name for the given doctype, name"""
	if sort_key not in ["is_shipping_address", "is_primary_address"]:
		return None

	out = dontmanage.db.sql(
		""" SELECT
			addr.name, addr.%s
		FROM
			`tabAddress` addr, `tabDynamic Link` dl
		WHERE
			dl.parent = addr.name and dl.link_doctype = %s and
			dl.link_name = %s and ifnull(addr.disabled, 0) = 0
		"""
		% (sort_key, "%s", "%s"),
		(doctype, name),
		as_dict=True,
	)

	if out:
		for contact in out:
			if contact.get(sort_key):
				return contact.name
		return out[0].name
	else:
		return None


@dontmanage.whitelist()
def get_address_display(address_dict):
	if not address_dict:
		return

	if not isinstance(address_dict, dict):
		address_dict = dontmanage.db.get_value("Address", address_dict, "*", as_dict=True, cache=True) or {}

	name, template = get_address_templates(address_dict)

	try:
		return dontmanage.render_template(template, address_dict)
	except TemplateSyntaxError:
		dontmanage.throw(_("There is an error in your Address Template {0}").format(name))


def get_territory_from_address(address):
	"""Tries to match city, state and country of address to existing territory"""
	if not address:
		return

	if isinstance(address, str):
		address = dontmanage.get_cached_doc("Address", address)

	territory = None
	for fieldname in ("city", "state", "country"):
		if address.get(fieldname):
			territory = dontmanage.db.get_value("Territory", address.get(fieldname))
			if territory:
				break

	return territory


def get_list_context(context=None):
	return {
		"title": _("Addresses"),
		"get_list": get_address_list,
		"row_template": "templates/includes/address_row.html",
		"no_breadcrumbs": True,
	}


def get_address_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by=None):
	from dontmanage.www.list import get_list

	user = dontmanage.session.user
	ignore_permissions = True

	if not filters:
		filters = []
	filters.append(("Address", "owner", "=", user))

	return get_list(
		doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions
	)


def has_website_permission(doc, ptype, user, verbose=False):
	"""Returns true if there is a related lead or contact related to this document"""
	contact_name = dontmanage.db.get_value("Contact", {"email_id": dontmanage.session.user})

	if contact_name:
		contact = dontmanage.get_doc("Contact", contact_name)
		return contact.has_common_link(doc)

	return False


def get_address_templates(address):
	result = dontmanage.db.get_value(
		"Address Template", {"country": address.get("country")}, ["name", "template"]
	)

	if not result:
		result = dontmanage.db.get_value("Address Template", {"is_default": 1}, ["name", "template"])

	if not result:
		dontmanage.throw(
			_(
				"No default Address Template found. Please create a new one from Setup > Printing and Branding > Address Template."
			)
		)
	else:
		return result


def get_company_address(company):
	ret = dontmanage._dict()
	ret.company_address = get_default_address("Company", company)
	ret.company_address_display = get_address_display(ret.company_address)

	return ret


@dontmanage.whitelist()
@dontmanage.validate_and_sanitize_search_inputs
def address_query(doctype, txt, searchfield, start, page_len, filters):
	from dontmanage.desk.reportview import get_match_cond

	doctype = "Address"
	link_doctype = filters.pop("link_doctype")
	link_name = filters.pop("link_name")

	condition = ""
	meta = dontmanage.get_meta(doctype)
	for fieldname, value in filters.items():
		if meta.get_field(fieldname) or fieldname in dontmanage.db.DEFAULT_COLUMNS:
			condition += f" and {fieldname}={dontmanage.db.escape(value)}"

	searchfields = meta.get_search_fields()

	if searchfield and (meta.get_field(searchfield) or searchfield in dontmanage.db.DEFAULT_COLUMNS):
		searchfields.append(searchfield)

	search_condition = ""
	for field in searchfields:
		if search_condition == "":
			search_condition += f"`tabAddress`.`{field}` like %(txt)s"
		else:
			search_condition += f" or `tabAddress`.`{field}` like %(txt)s"

	return dontmanage.db.sql(
		"""select
			`tabAddress`.name, `tabAddress`.city, `tabAddress`.country
		from
			`tabAddress`, `tabDynamic Link`
		where
			`tabDynamic Link`.parent = `tabAddress`.name and
			`tabDynamic Link`.parenttype = 'Address' and
			`tabDynamic Link`.link_doctype = %(link_doctype)s and
			`tabDynamic Link`.link_name = %(link_name)s and
			ifnull(`tabAddress`.disabled, 0) = 0 and
			({search_condition})
			{mcond} {condition}
		order by
			if(locate(%(_txt)s, `tabAddress`.name), locate(%(_txt)s, `tabAddress`.name), 99999),
			`tabAddress`.idx desc, `tabAddress`.name
		limit %(start)s, %(page_len)s """.format(
			mcond=get_match_cond(doctype),
			search_condition=search_condition,
			condition=condition or "",
		),
		{
			"txt": "%" + txt + "%",
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len,
			"link_name": link_name,
			"link_doctype": link_doctype,
		},
	)


def get_condensed_address(doc):
	fields = ["address_title", "address_line1", "address_line2", "city", "county", "state", "country"]
	return ", ".join(doc.get(d) for d in fields if doc.get(d))


def update_preferred_address(address, field):
	dontmanage.db.set_value("Address", address, field, 0)

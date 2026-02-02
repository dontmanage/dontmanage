# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model import is_default_field
from dontmanage.query_builder import Order
from dontmanage.query_builder.functions import Count
from dontmanage.query_builder.terms import SubQuery
from dontmanage.query_builder.utils import DocType


@dontmanage.whitelist()
def get_list_settings(doctype):
	try:
		return dontmanage.get_cached_doc("List View Settings", doctype)
	except dontmanage.DoesNotExistError:
		dontmanage.clear_messages()


@dontmanage.whitelist()
def set_list_settings(doctype, values):
	try:
		doc = dontmanage.get_doc("List View Settings", doctype)
	except dontmanage.DoesNotExistError:
		doc = dontmanage.new_doc("List View Settings")
		doc.name = doctype
		dontmanage.clear_messages()
	doc.update(dontmanage.parse_json(values))
	doc.save()


@dontmanage.whitelist()
def get_group_by_count(doctype: str, current_filters: str, field: str) -> list[dict]:
	current_filters = dontmanage.parse_json(current_filters)

	if field == "assigned_to":
		ToDo = DocType("ToDo")
		User = DocType("User")
		count = Count("*").as_("count")
		filtered_records = dontmanage.qb.get_query(
			doctype,
			filters=current_filters,
			fields=["name"],
			ignore_permissions=False,
		)

		return (
			dontmanage.qb.from_(ToDo)
			.from_(User)
			.select(ToDo.allocated_to.as_("name"), count)
			.where(
				(ToDo.status != "Cancelled")
				& (ToDo.allocated_to == User.name)
				& (User.user_type == "System User")
				& (ToDo.reference_name.isin(SubQuery(filtered_records)))
			)
			.groupby(ToDo.allocated_to)
			.orderby(count, order=Order.desc)
			.limit(50)
			.run(as_dict=True)
		)

	meta = dontmanage.get_meta(doctype)

	if not meta.has_field(field) and not is_default_field(field):
		raise ValueError("Field does not belong to doctype")

	data = dontmanage.get_list(
		doctype,
		filters=current_filters,
		group_by=field,
		fields=[{"COUNT": "*", "as": "count"}, f"{field} as name"],
		order_by="count desc",
		limit=1000,
	)

	if field == "owner":
		owner_idx = None

		for idx, item in enumerate(data):
			if item.name == dontmanage.session.user:
				owner_idx = idx
				break

		if owner_idx:
			data = [data.pop(owner_idx), *data[0:49]]
		else:
			data = data[0:50]
	else:
		data = data[0:50]

	# Add in title if it's a link field and `show_title_field_in_link` is set
	if (field_meta := meta.get_field(field)) and field_meta.fieldtype == "Link":
		link_meta = dontmanage.get_meta(field_meta.options)
		if link_meta.show_title_field_in_link:
			title_field = link_meta.get_title_field()
			for item in data:
				item.title = dontmanage.get_value(field_meta.options, item.name, title_field)

	return data

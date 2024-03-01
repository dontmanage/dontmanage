# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
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
		filtered_records = dontmanage.qb.engine.build_conditions(doctype, current_filters).select("name")

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

	return dontmanage.get_list(
		doctype,
		filters=current_filters,
		group_by=f"`tab{doctype}`.{field}",
		fields=["count(*) as count", f"`{field}` as name"],
		order_by="count desc",
		limit=50,
	)
# Copyright (c) 2022, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.deferred_insert import deferred_insert as _deferred_insert
from dontmanage.model.document import Document


class RouteHistory(Document):
	@staticmethod
	def clear_old_logs(days=30):
		from dontmanage.query_builder import Interval
		from dontmanage.query_builder.functions import Now

		table = dontmanage.qb.DocType("Route History")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@dontmanage.whitelist()
def deferred_insert(routes):
	routes = [
		{
			"user": dontmanage.session.user,
			"route": route.get("route"),
			"creation": route.get("creation"),
		}
		for route in dontmanage.parse_json(routes)
	]

	_deferred_insert("Route History", routes)


@dontmanage.whitelist()
def frequently_visited_links():
	return dontmanage.get_all(
		"Route History",
		fields=["route", "count(name) as count"],
		filters={"user": dontmanage.session.user},
		group_by="route",
		order_by="count desc",
		limit=5,
	)

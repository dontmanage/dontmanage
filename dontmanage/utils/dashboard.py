# Copyright (c) 2019, DontManage and Contributors
# License: MIT. See LICENSE
import os
from functools import wraps
from os.path import join

import dontmanage
from dontmanage import _
from dontmanage.modules.import_file import import_file_by_path
from dontmanage.utils import cint, get_link_to_form


def cache_source(function):
	@wraps(function)
	def wrapper(*args, **kwargs):
		if kwargs.get("chart_name"):
			chart = dontmanage.get_doc("Dashboard Chart", kwargs.get("chart_name"))
		else:
			chart = kwargs.get("chart")
		no_cache = kwargs.get("no_cache")
		if no_cache:
			return function(chart=chart, no_cache=no_cache)
		chart_name = dontmanage.parse_json(chart).name
		cache_key = f"chart-data:{chart_name}"
		if int(kwargs.get("refresh") or 0):
			results = generate_and_cache_results(kwargs, function, cache_key, chart)
		else:
			cached_results = dontmanage.cache().get_value(cache_key)
			if cached_results:
				results = dontmanage.parse_json(dontmanage.safe_decode(cached_results))
			else:
				results = generate_and_cache_results(kwargs, function, cache_key, chart)
		return results

	return wrapper


def generate_and_cache_results(args, function, cache_key, chart):
	try:
		args = dontmanage._dict(args)
		results = function(
			chart_name=args.chart_name,
			filters=args.filters or None,
			from_date=args.from_date or None,
			to_date=args.to_date or None,
			time_interval=args.time_interval or None,
			timespan=args.timespan or None,
			heatmap_year=args.heatmap_year or None,
		)
	except TypeError as e:
		if str(e) == "'NoneType' object is not iterable":
			# Probably because of invalid link filter
			#
			# Note: Do not try to find the right way of doing this because
			# it results in an inelegant & inefficient solution
			# ref: https://github.com/dontmanage/dontmanage/pull/9403
			dontmanage.throw(
				_("Please check the filter values set for Dashboard Chart: {}").format(
					get_link_to_form(chart.doctype, chart.name)
				),
				title=_("Invalid Filter Value"),
			)
			return
		else:
			raise

	if not dontmanage.flags.read_only:
		dontmanage.db.set_value(
			"Dashboard Chart", args.chart_name, "last_synced_on", dontmanage.utils.now(), update_modified=False
		)
	return results


def get_dashboards_with_link(docname, doctype):
	dashboards = []
	links = []

	if doctype == "Dashboard Chart":
		links = dontmanage.get_all("Dashboard Chart Link", fields=["parent"], filters={"chart": docname})
	elif doctype == "Number Card":
		links = dontmanage.get_all("Number Card Link", fields=["parent"], filters={"card": docname})

	dashboards = [link.parent for link in links]
	return dashboards


def sync_dashboards(app=None):
	"""Import, overwrite dashboards from `[app]/[app]_dashboard`"""
	apps = [app] if app else dontmanage.get_installed_apps()

	for app_name in apps:
		print(f"Updating Dashboard for {app_name}")
		for module_name in dontmanage.local.app_modules.get(app_name) or []:
			dontmanage.flags.in_import = True
			make_records_in_module(app_name, module_name)
			dontmanage.flags.in_import = False


def make_records_in_module(app, module):
	dashboards_path = dontmanage.get_module_path(module, f"{module}_dashboard")
	charts_path = dontmanage.get_module_path(module, "dashboard chart")
	cards_path = dontmanage.get_module_path(module, "number card")

	paths = [dashboards_path, charts_path, cards_path]
	for path in paths:
		make_records(path)


def make_records(path, filters=None):
	if os.path.isdir(path):
		for fname in os.listdir(path):
			if os.path.isdir(join(path, fname)):
				if fname == "__pycache__":
					continue
				import_file_by_path("{path}/{fname}/{fname}.json".format(path=path, fname=fname))

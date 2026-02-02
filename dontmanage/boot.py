# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
"""
bootstrap client session
"""

import os

import dontmanage
import dontmanage.defaults
import dontmanage.desk.desk_page
from dontmanage.core.doctype.installed_applications.installed_applications import (
	get_setup_wizard_completed_apps,
)
from dontmanage.core.doctype.navbar_settings.navbar_settings import get_app_logo, get_navbar_settings
from dontmanage.desk.doctype.changelog_feed.changelog_feed import get_changelog_feed_items
from dontmanage.desk.doctype.desktop_icon.desktop_icon import get_desktop_icons
from dontmanage.desk.doctype.form_tour.form_tour import get_onboarding_ui_tours
from dontmanage.desk.doctype.route_history.route_history import frequently_visited_links
from dontmanage.desk.form.load import get_meta_bundle
from dontmanage.email.inbox import get_email_accounts
from dontmanage.integrations.dontmanage_providers.dontmanagecloud_billing import is_fc_site
from dontmanage.model.base_document import get_controller
from dontmanage.permissions import has_permission
from dontmanage.query_builder import DocType
from dontmanage.query_builder.functions import Count
from dontmanage.query_builder.terms import ParameterizedValueWrapper, SubQuery
from dontmanage.utils import add_user_info, cstr, get_system_timezone
from dontmanage.utils.change_log import get_versions
from dontmanage.utils.dontmanagecloud import on_dontmanagecloud
from dontmanage.website.doctype.web_page_view.web_page_view import is_tracking_enabled


def get_bootinfo():
	"""build and return boot info"""
	from dontmanage.translate import get_lang_dict, get_translated_doctypes

	dontmanage.set_user_lang(dontmanage.session.user)
	bootinfo = dontmanage._dict()
	hooks = dontmanage.get_hooks()
	doclist = []

	# user
	get_user(bootinfo)
	# desktop icon info

	# system info
	bootinfo.sitename = dontmanage.local.site
	bootinfo.sysdefaults = dontmanage.defaults.get_defaults()
	bootinfo.sysdefaults["setup_complete"] = dontmanage.is_setup_complete()

	bootinfo.server_date = dontmanage.utils.nowdate()

	if dontmanage.session["user"] != "Guest":
		bootinfo.user_info = get_user_info()

	bootinfo.modules = {}
	bootinfo.module_list = []
	load_desktop_data(bootinfo)
	bootinfo.desktop_icons = get_desktop_icons(bootinfo=bootinfo)
	bootinfo.letter_heads = get_letter_heads()
	bootinfo.active_domains = dontmanage.get_active_domains()
	bootinfo.all_domains = [d.get("name") for d in dontmanage.get_all("Domain")]
	add_layouts(bootinfo)

	bootinfo.module_app = dontmanage.local.module_app
	bootinfo.single_types = [d.name for d in dontmanage.get_all("DocType", {"issingle": 1})]
	bootinfo.nested_set_doctypes = [
		d.parent for d in dontmanage.get_all("DocField", {"fieldname": "lft"}, ["parent"])
	]
	add_home_page(bootinfo, doclist)
	bootinfo.page_info = get_allowed_pages()
	load_translations(bootinfo)
	add_timezone_info(bootinfo)
	load_conf_settings(bootinfo)
	load_print(bootinfo, doclist)
	doclist.extend(get_meta_bundle("Page"))
	bootinfo.home_folder = dontmanage.db.get_value("File", {"is_home_folder": 1})
	bootinfo.navbar_settings = get_navbar_settings()
	bootinfo.notification_settings = get_notification_settings()
	bootinfo.onboarding_tours = get_onboarding_ui_tours()
	set_time_zone(bootinfo)

	# ipinfo
	if dontmanage.session.data.get("ipinfo"):
		bootinfo.ipinfo = dontmanage.session["data"]["ipinfo"]

	# add docs
	bootinfo.docs = doclist
	load_country_doc(bootinfo)
	load_currency_docs(bootinfo)

	for method in hooks.boot_session or []:
		dontmanage.get_attr(method)(bootinfo)

	if bootinfo.lang:
		bootinfo.lang = str(bootinfo.lang)
	bootinfo.versions = {k: v["version"] for k, v in get_versions().items()}

	bootinfo.error_report_email = dontmanage.conf.error_report_email
	bootinfo.calendars = sorted(dontmanage.get_hooks("calendars"))
	bootinfo.treeviews = dontmanage.get_hooks("treeviews") or []
	bootinfo.lang_dict = get_lang_dict()
	bootinfo.success_action = get_success_action()
	bootinfo.update(get_email_accounts(user=dontmanage.session.user))
	bootinfo.sms_gateway_enabled = bool(dontmanage.db.get_single_value("SMS Settings", "sms_gateway_url"))
	bootinfo.frequently_visited_links = frequently_visited_links()
	bootinfo.link_preview_doctypes = get_link_preview_doctypes()
	bootinfo.additional_filters_config = get_additional_filters_from_hooks()
	bootinfo.desk_settings = get_desk_settings()
	bootinfo.app_logo_url = get_app_logo()
	bootinfo.link_title_doctypes = get_link_title_doctypes()
	bootinfo.translated_doctypes = get_translated_doctypes()
	bootinfo.subscription_conf = add_subscription_conf()
	bootinfo.marketplace_apps = get_marketplace_apps()
	bootinfo.is_fc_site = is_fc_site()
	bootinfo.changelog_feed = get_changelog_feed_items()
	bootinfo.enable_address_autocompletion = dontmanage.db.get_single_value(
		"Geolocation Settings", "enable_address_autocompletion"
	)

	if sentry_dsn := get_sentry_dsn():
		bootinfo.sentry_dsn = sentry_dsn

	bootinfo.setup_wizard_completed_apps = get_setup_wizard_completed_apps() or []
	bootinfo.desktop_icon_urls = get_desktop_icon_urls()
	bootinfo.desktop_icon_style = get_icon_style() or "Subtle"
	return bootinfo


def get_icon_style():
	icon_style = dontmanage.db.get_single_value("Desktop Settings", "icon_style")
	if icon_style not in ["Subtle", "Solid"]:
		return "Solid"
	return icon_style


def get_letter_heads():
	letter_heads = {}

	if not dontmanage.has_permission("Letter Head"):
		return letter_heads
	for letter_head in dontmanage.get_list("Letter Head", fields=["name", "content", "footer"]):
		letter_heads.setdefault(
			letter_head.name, {"header": letter_head.content, "footer": letter_head.footer}
		)

	return letter_heads


def load_conf_settings(bootinfo):
	from dontmanage.core.api.file import get_max_file_size

	bootinfo.max_file_size = get_max_file_size()
	for key in ("developer_mode", "socketio_port", "file_watcher_port"):
		if key in dontmanage.conf:
			bootinfo[key] = dontmanage.conf.get(key)


def load_desktop_data(bootinfo):
	from dontmanage.desk.desktop import get_workspace_sidebar_items

	bootinfo.workspaces = get_workspace_sidebar_items()
	allowed_pages = [d.name for d in bootinfo.workspaces.get("pages")]
	bootinfo.workspace_sidebar_item = get_sidebar_items(allowed_pages)
	bootinfo.module_wise_workspaces = get_controller("Workspace").get_module_wise_workspaces()
	bootinfo.dashboards = dontmanage.get_all("Dashboard")
	bootinfo.app_data = []

	Workspace = dontmanage.qb.DocType("Workspace")
	Module = dontmanage.qb.DocType("Module Def")

	for app_name in dontmanage.get_installed_apps():
		# get app details from app_info (/apps)
		apps = dontmanage.get_hooks("add_to_apps_screen", app_name=app_name)
		app_info = {}
		if apps:
			app_info = apps[0]
			has_permission = app_info.get("has_permission")
			if has_permission and not dontmanage.get_attr(has_permission)():
				continue

		workspaces = [
			r[0]
			for r in (
				dontmanage.qb.from_(Workspace)
				.inner_join(Module)
				.on(Workspace.module == Module.name)
				.select(Workspace.name)
				.where(Module.app_name == app_name)
				.run()
			)
			if r[0] in allowed_pages
		]

		bootinfo.app_data.append(
			dict(
				app_name=app_info.get("name") or app_name,
				app_title=app_info.get("title")
				or (
					(
						dontmanage.get_hooks("app_title", app_name=app_name)
						and dontmanage.get_hooks("app_title", app_name=app_name)[0]
					)
					or ""
				)
				or app_name,
				app_route=(
					dontmanage.get_hooks("app_home", app_name=app_name)
					and dontmanage.get_hooks("app_home", app_name=app_name)[0]
				)
				or (workspaces and "/desk/" + dontmanage.utils.slug(workspaces[0]))
				or "",
				app_logo_url=app_info.get("logo")
				or dontmanage.get_hooks("app_logo_url", app_name=app_name)
				or dontmanage.get_hooks("app_logo_url", app_name="dontmanage"),
				modules=[m.name for m in dontmanage.get_all("Module Def", dict(app_name=app_name))],
				workspaces=workspaces,
			)
		)


def get_allowed_pages(cache=False):
	return get_user_pages_or_reports("Page", cache=cache)


def get_allowed_reports(cache=False):
	return get_user_pages_or_reports("Report", cache=cache)


def get_allowed_report_names(cache=False) -> set[str]:
	return {cstr(report) for report in get_allowed_reports(cache).keys() if report}


def get_user_pages_or_reports(parent, cache=False):
	if cache:
		has_role = dontmanage.cache.get_value("has_role:" + parent, user=dontmanage.session.user)
		if has_role:
			return has_role

	roles = dontmanage.get_roles()
	has_role = {}

	page = DocType("Page")
	report = DocType("Report")

	is_report = parent == "Report"

	if is_report:
		columns = (report.name.as_("title"), report.ref_doctype, report.report_type)
	else:
		columns = (page.title.as_("title"),)

	customRole = DocType("Custom Role")
	hasRole = DocType("Has Role")
	parentTable = DocType(parent)

	# get pages or reports set on custom role
	pages_with_custom_roles = (
		dontmanage.qb.from_(customRole)
		.from_(hasRole)
		.from_(parentTable)
		.select(customRole[parent.lower()].as_("name"), customRole.modified, customRole.ref_doctype, *columns)
		.where(
			(hasRole.parent == customRole.name)
			& (parentTable.name == customRole[parent.lower()])
			& (customRole[parent.lower()].isnotnull())
			& (hasRole.role.isin(roles))
		)
	).run(as_dict=True)

	for p in pages_with_custom_roles:
		has_role[p.name] = {"modified": p.modified, "title": p.title, "ref_doctype": p.ref_doctype}

	subq = (
		dontmanage.qb.from_(customRole)
		.select(customRole[parent.lower()])
		.where(customRole[parent.lower()].isnotnull())
	)

	pages_with_standard_roles = (
		dontmanage.qb.from_(hasRole)
		.from_(parentTable)
		.select(parentTable.name.as_("name"), parentTable.modified, *columns)
		.where(
			(hasRole.role.isin(roles)) & (hasRole.parent == parentTable.name) & (parentTable.name.notin(subq))
		)
		.distinct()
	)

	if is_report:
		pages_with_standard_roles = pages_with_standard_roles.where(report.disabled == 0)

	pages_with_standard_roles = pages_with_standard_roles.run(as_dict=True)

	for p in pages_with_standard_roles:
		if p.name not in has_role:
			has_role[p.name] = {"modified": p.modified, "title": p.title}
			if parent == "Report":
				has_role[p.name].update({"ref_doctype": p.ref_doctype})

	no_of_roles = SubQuery(
		dontmanage.qb.from_(hasRole).select(Count("*")).where(hasRole.parent == parentTable.name)
	)

	# pages and reports with no role are allowed
	rows_with_no_roles = (
		dontmanage.qb.from_(parentTable)
		.select(parentTable.name, parentTable.modified, *columns)
		.where(no_of_roles == 0)
	).run(as_dict=True)

	for r in rows_with_no_roles:
		if r.name not in has_role:
			has_role[r.name] = {"modified": r.modified, "title": r.title}
			if is_report:
				has_role[r.name] |= {"ref_doctype": r.ref_doctype}

	if is_report:
		if not has_permission("Report", print_logs=False):
			return {}

		reports = dontmanage.get_list(
			"Report",
			fields=["name", "report_type"],
			filters={"name": ("in", has_role.keys())},
			ignore_ifnull=True,
		)
		for report in reports:
			has_role[report.name]["report_type"] = report.report_type

		non_permitted_reports = set(has_role.keys()) - {r.name for r in reports}
		for r in non_permitted_reports:
			has_role.pop(r, None)

	# Expire every six hours
	dontmanage.cache.set_value("has_role:" + parent, has_role, dontmanage.session.user, 21600)
	return has_role


def load_translations(bootinfo):
	from dontmanage.translate import get_messages_for_boot

	bootinfo["lang"] = dontmanage.lang
	bootinfo["__messages"] = get_messages_for_boot()


def get_user_info():
	# get info for current user
	user_info = dontmanage._dict()
	add_user_info(dontmanage.session.user, user_info)

	return user_info


def get_user(bootinfo):
	"""get user info"""
	bootinfo.user = dontmanage.get_user().load_user()


def add_home_page(bootinfo, docs):
	"""load home page"""
	if dontmanage.session.user == "Guest":
		return
	home_page = dontmanage.db.get_default("desktop:home_page")

	if not dontmanage.is_setup_complete():
		bootinfo.setup_wizard_requires = dontmanage.get_hooks("setup_wizard_requires")

	try:
		page = dontmanage.desk.desk_page.get(home_page)
		docs.append(page)
		bootinfo["home_page"] = page.name
	except (dontmanage.DoesNotExistError, dontmanage.PermissionError):
		dontmanage.clear_last_message()
		bootinfo["home_page"] = "desktop"


def add_timezone_info(bootinfo):
	system = bootinfo.sysdefaults.get("time_zone")
	import dontmanage.utils.momentjs

	bootinfo.timezone_info = {"zones": {}, "rules": {}, "links": {}}
	dontmanage.utils.momentjs.update(system, bootinfo.timezone_info)


def load_print(bootinfo, doclist):
	print_settings = dontmanage.db.get_singles_dict("Print Settings")
	print_settings.doctype = ":Print Settings"
	doclist.append(print_settings)
	load_print_css(bootinfo, print_settings)


def load_print_css(bootinfo, print_settings):
	import dontmanage.www.printview

	bootinfo.print_css = dontmanage.www.printview.get_print_style(
		print_settings.print_style or "Redesign", for_legacy=True
	)


def get_success_action():
	return dontmanage.get_all("Success Action", fields=["*"])


def get_link_preview_doctypes():
	from dontmanage.utils import cint

	link_preview_doctypes = [d.name for d in dontmanage.get_all("DocType", {"show_preview_popup": 1})]
	customizations = dontmanage.get_all(
		"Property Setter", fields=["doc_type", "value"], filters={"property": "show_preview_popup"}
	)

	for custom in customizations:
		if not cint(custom.value) and custom.doc_type in link_preview_doctypes:
			link_preview_doctypes.remove(custom.doc_type)
		else:
			link_preview_doctypes.append(custom.doc_type)

	return link_preview_doctypes


def get_additional_filters_from_hooks():
	filter_config = dontmanage._dict()
	filter_hooks = dontmanage.get_hooks("filters_config")
	for hook in filter_hooks:
		filter_config.update(dontmanage.get_attr(hook)())

	return filter_config


def add_layouts(bootinfo):
	# add routes for readable doctypes
	bootinfo.doctype_layouts = dontmanage.get_all("DocType Layout", ["name", "route", "document_type"])


def get_desk_settings():
	from dontmanage.core.doctype.user.user import desk_properties

	return dontmanage.get_value("User", dontmanage.session.user, desk_properties, as_dict=True)


def get_notification_settings():
	return dontmanage.get_cached_doc("Notification Settings", dontmanage.session.user)


def get_link_title_doctypes():
	dts = dontmanage.get_all("DocType", {"show_title_field_in_link": 1})
	custom_dts = dontmanage.get_all(
		"Property Setter",
		{"property": "show_title_field_in_link", "value": "1"},
		["doc_type as name"],
	)
	return [d.name for d in dts + custom_dts if d]


def set_time_zone(bootinfo):
	bootinfo.time_zone = {
		"system": get_system_timezone(),
		"user": bootinfo.get("user_info", {}).get(dontmanage.session.user, {}).get("time_zone", None)
		or get_system_timezone(),
	}


def load_country_doc(bootinfo):
	country = dontmanage.db.get_default("country")
	if not country:
		return
	try:
		bootinfo.docs.append(dontmanage.get_cached_doc("Country", country))
	except Exception:
		pass


def load_currency_docs(bootinfo):
	currency = dontmanage.qb.DocType("Currency")

	currency_docs = (
		dontmanage.qb.from_(currency)
		.select(
			currency.name,
			currency.fraction,
			currency.fraction_units,
			currency.number_format,
			currency.smallest_currency_fraction_value,
			currency.symbol,
			currency.symbol_on_right,
		)
		.where(currency.enabled == 1)
		.run(as_dict=1, update={"doctype": ":Currency"})
	)

	bootinfo.docs += currency_docs


def get_marketplace_apps():
	import requests

	apps = []
	cache_key = "dontmanage_marketplace_apps"

	if dontmanage.conf.developer_mode or not on_dontmanagecloud():
		return apps

	def get_apps_from_fc():
		remote_site = dontmanage.conf.dontmanagecloud_url or "dontmanagecloud.com"
		request_url = f"https://{remote_site}/api/method/press.api.marketplace.get_marketplace_apps"
		request = requests.get(request_url, timeout=2.0)
		return request.json()["message"]

	try:
		apps = dontmanage.cache.get_value(cache_key, get_apps_from_fc, shared=True)
		installed_apps = set(dontmanage.get_installed_apps())
		apps = [app for app in apps if app["name"] not in installed_apps]
	except Exception:
		# Don't retry for a day
		dontmanage.cache.set_value(cache_key, apps, shared=True, expires_in_sec=24 * 60 * 60)

	return apps


def add_subscription_conf():
	try:
		return dontmanage.conf.subscription
	except Exception:
		return ""


def get_sentry_dsn():
	if not dontmanage.get_system_settings("enable_telemetry"):
		return

	return os.getenv("DONTMANAGE_SENTRY_DSN")


def get_sidebar_items(allowed_workspaces):
	from dontmanage import _
	from dontmanage.desk.doctype.workspace_sidebar.workspace_sidebar import auto_generate_sidebar_from_module

	sidebars = dontmanage.get_all("Workspace Sidebar", fields=["name", "header_icon"])
	module_sidebars = auto_generate_sidebar_from_module()
	sidebars.extend(module_sidebars)
	sidebar_items = {}

	for s in sidebars:
		sidebar_title = s.get("name")
		if sidebar_title:
			w = dontmanage.get_doc("Workspace Sidebar", sidebar_title)
		else:
			sidebar_title = s.title
			w = s
		sidebar_items[sidebar_title.lower()] = {
			"label": sidebar_title,
			"items": [],
			"header_icon": s.get("header_icon"),
			"module": w.module,
			"app": w.app,
		}
		for si in w.items:
			workspace_sidebar = {
				"label": _(si.label),
				"link_to": si.link_to,
				"link_type": si.link_type,
				"type": si.type,
				"icon": si.icon,
				"child": si.child,
				"collapsible": si.collapsible,
				"indent": si.indent,
				"keep_closed": si.keep_closed,
				"display_depends_on": si.display_depends_on,
				"url": si.url,
				"show_arrow": si.show_arrow,
				"filters": si.filters,
				"route_options": si.route_options,
				"tab": si.navigate_to_tab,
			}
			if si.link_type == "Report" and si.link_to and dontmanage.db.exists("Report", si.link_to):
				report_type, ref_doctype = dontmanage.db.get_value(
					"Report", si.link_to, ["report_type", "ref_doctype"]
				)
				workspace_sidebar["report"] = {
					"report_type": report_type,
					"ref_doctype": ref_doctype,
				}
			if (
				"My Workspaces" in sidebar_title
				or si.type == "Section Break"
				or w.is_item_allowed(si.link_to, si.link_type, allowed_workspaces)
			):
				sidebar_items[sidebar_title.lower()]["items"].append(workspace_sidebar)
	add_user_specific_sidebar(sidebar_items)
	return sidebar_items


def get_desktop_icon_urls():
	icons_map = {}

	for app in dontmanage.get_installed_apps():
		app_path = dontmanage.get_app_path(app)
		icons_dir = os.path.join(app_path, "public", "icons", "desktop_icons")

		if not os.path.exists(icons_dir):
			continue

		icons_map[app] = {"subtle": [], "solid": []}

		for variant in ["subtle", "solid"]:
			variant_path = os.path.join(icons_dir, variant)

			if os.path.exists(variant_path):
				for fname in os.listdir(variant_path):
					if fname.endswith(".svg"):
						abs_path = os.path.join(variant_path, fname)
						assets_path = abs_path.replace(
							os.path.join(app_path, "public"), os.path.join("assets", app)
						)
						icons_map[app][variant].append(assets_path)

	return icons_map


def add_user_specific_sidebar(sidebar_items):
	sidebars_to_remove = []
	for sidebar in sidebar_items.keys():
		if f"-{dontmanage.session.user.lower()}" in sidebar:
			sidebars_to_remove.append(sidebar)
	for sidebar in sidebars_to_remove:
		try:
			sidebar_name = sidebar.replace(f"-{dontmanage.session.user.lower()}", "")
			sidebar_items[sidebar]["label"] = sidebar_items[sidebar_name]["label"]
			sidebar_items[sidebar_name] = sidebar_items.pop(sidebar)
		except KeyError:
			pass

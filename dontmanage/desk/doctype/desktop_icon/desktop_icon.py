# Copyright (c) 2015, DontManage and contributors
# License: MIT. See LICENSE

import json
import os
import random

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.modules.export_file import strip_default_fields
from dontmanage.modules.import_file import import_file_by_path
from dontmanage.modules.utils import create_directory_on_app_path, get_app_level_directory_path


class DesktopIcon(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.core.doctype.has_role.has_role import HasRole
		from dontmanage.types import DF

		app: DF.Autocomplete | None
		bg_color: DF.Literal["blue", "gray"]
		hidden: DF.Check
		icon_image: DF.Attach | None
		icon_type: DF.Literal["Link", "Folder", "App"]
		idx: DF.Int
		label: DF.Data | None
		link: DF.SmallText | None
		link_to: DF.DynamicLink | None
		link_type: DF.Literal["Workspace Sidebar", "External"]
		logo_url: DF.Data | None
		parent_icon: DF.Link | None
		restrict_removal: DF.Check
		roles: DF.Table[HasRole]
		sidebar: DF.Link | None
		standard: DF.Check
	# end: auto-generated types

	def validate(self):
		if not self.label:
			self.label = self.module_name

	def on_trash(self):
		clear_desktop_icons_cache()
		if dontmanage.conf.developer_mode and self.standard and self.app:
			delete_desktop_icon_file(self.app, self.label)

	def check_for_restrict_removal(self):
		if self.restrict_removal:
			dontmanage.throw(_("Cannot delete Desktop Icon '{0}' as it is restricted").format(self.label))

	def on_update(self):
		self.export_desktop_icon()

	def after_rename(self, old, new, merge):
		delete_desktop_icon_file(self.app, old)
		self.export_desktop_icon()

	def export_desktop_icon(self):
		allow_export = (
			self.standard and self.app and not dontmanage.flags.in_import and dontmanage.conf.developer_mode
		)
		if allow_export:
			folder_path = create_directory_on_app_path("desktop_icon", self.app)
			file_path = os.path.join(folder_path, f"{dontmanage.scrub(self.label)}.json")
			doc_export = self.as_dict(no_nulls=True, no_private_properties=True)
			strip_default_fields(self, doc_export)
			with open(file_path, "w+") as icon_file_doc:
				icon_file_doc.write(dontmanage.as_json(doc_export) + "\n")

	def delete_desktop_icon_file(self):
		folder_path = create_directory_on_app_path("desktop_icon", self.app)
		file_path = os.path.join(folder_path, f"{dontmanage.scrub(self.label)}.json")
		if os.path.exists(file_path):
			os.remove(file_path)

	def is_permitted(self, bootinfo):
		icon_module = None
		if self.icon_type == "Link" and self.link_to:
			icon_module = dontmanage.db.get_value("Workspace", self.link_to, "module")
		# module permission check
		if icon_module:
			blocked_modules = dontmanage.get_cached_doc("User", dontmanage.session.user).get_blocked_modules()
			if icon_module in blocked_modules:
				return False
		# perform a permission check based on roles table (desktop icons)
		allowed_roles = [d.role for d in self.get("roles") or []]
		if allowed_roles and not set(allowed_roles).intersection(dontmanage.get_roles()):
			return False
		if self.icon_type == "Folder":
			return True
		elif self.icon_type == "App":
			return self.check_app_permission()
		else:
			try:
				items = bootinfo.workspace_sidebar_item[self.label.lower()]["items"]

				if len(items) and all(item["type"] == "Section Break" for item in items):
					return False

				return True
			except KeyError:
				return True

	def check_app_permission(self):
		for a in dontmanage.get_installed_apps():
			if dontmanage.get_hooks(app_name=a)["app_title"][0] == self.label or self.app == a:
				permission_method = dontmanage.get_hooks(app_name=a)["add_to_apps_screen"][0].get(
					"has_permission", None
				)
				if permission_method:
					return dontmanage.call(permission_method)
				else:
					return True

	# def is_permitted(self):
	# 	"""Return True if `Has Role` is not set or the user is allowed."""
	# 	from dontmanage.utils import has_common

	# 	allowed = [d.role for d in dontmanage.get_all("Has Role", fields=["role"], filters={"parent": self.name})]

	# 	if not allowed:
	# 		return True

	# 	roles = dontmanage.get_roles()

	# 	if has_common(roles, allowed):
	# 		return True

	def after_insert(self):
		clear_desktop_icons_cache()


def delete_desktop_icon_file(app, label):
	folder_path = create_directory_on_app_path("desktop_icon", app)
	file_path = os.path.join(folder_path, f"{dontmanage.scrub(label)}.json")
	if os.path.exists(file_path):
		os.remove(file_path)


def get_workspace_names(workspaces):
	workspace_list = []
	for w in workspaces["pages"]:
		workspace_list.append(w["name"])
	return workspace_list


def get_desktop_icons(user=None, bootinfo=None):
	"""Return desktop icons for user"""
	if not user:
		user = dontmanage.session.user

	user_icons = dontmanage.cache.hget("desktop_icons", user)

	if not user_icons:
		fields = [
			"label",
			"bg_color",
			"link",
			"link_type",
			"app",
			"icon_type",
			"parent_icon",
			"icon",
			"link_to",
			"idx",
			"standard",
			"logo_url",
			"hidden",
			"name",
			"restrict_removal",
			"icon_image",
		]

		from dontmanage.query_builder import DocType

		DesktopIcon = DocType("Desktop Icon")

		user_icons = (
			dontmanage.qb.from_(DesktopIcon)
			.select(*fields)
			.where(
				(DesktopIcon.standard == 1)
				| (
					(DesktopIcon.standard == 0)
					& (DesktopIcon.owner.isin(["Administrator", dontmanage.session.user]))
				)
			)
			.distinct()
		).run(as_dict=True)

		# sort by idx
		user_icons.sort(key=lambda a: a.idx)

		permitted_icons = []
		permitted_parent_labels = set()
		if bootinfo:
			for s in user_icons:
				icon = dontmanage.get_doc("Desktop Icon", s)
				if icon.is_permitted(bootinfo):
					permitted_icons.append(s)

				if not s.parent_icon:
					permitted_parent_labels.add(s.label)

		user_icons = [
			s for s in permitted_icons if not s.parent_icon or s.parent_icon in permitted_parent_labels
		]

		dontmanage.cache.hset("desktop_icons", user, user_icons)
	return user_icons


def clear_desktop_icons_cache(user=None):
	dontmanage.cache.hdel("desktop_icons", user or dontmanage.session.user)
	dontmanage.cache.hdel("bootinfo", user or dontmanage.session.user)


def create_desktop_icons_from_workspace():
	workspaces = dontmanage.get_all(
		"Workspace",
		filters={"public": 1, "name": ["!=", "Welcome Workspace"]},
		fields=["name", "icon", "app", "module"],
	)

	for w in workspaces:
		icon = dontmanage.new_doc("Desktop Icon")
		icon.link_type = "Workspace Sidebar"
		icon.label = w.name
		icon.icon_type = "Link"
		icon.link_to = w.name
		icon.icon = w.icon
		if w.module:
			app_name = w.app or dontmanage.db.get_value("Module Def", w.module, "app_name")
			if app_name in dontmanage.get_installed_apps():
				icon.app_name = app_name
				app_title = dontmanage.get_hooks("app_title", app_name=app_name)[0]
				app_icon = dontmanage.db.exists("Desktop Icon", {"label": app_title, "icon_type": "App"})
				if app_icon:
					icon.parent_icon = app_icon

				# Portal App With Desk Workspace
				if dontmanage.db.get_value("Desktop Icon", app_icon, "link") and not dontmanage.db.get_value(
					"Desktop Icon", app_icon, "link"
				).startswith("/app"):
					icon.hidden = 1
					icon.parent_icon = None

				# If Desk App has one workspace with the same name
				if icon.label == app_title and (
					app_icon and dontmanage.db.get_value("Desktop Icon", app_icon, "link").startswith("/app")
				):
					icon.hidden = 1
					icon.parent_icon = None

				try:
					if not dontmanage.db.exists(
						"Desktop Icon", [{"label": icon.label, "icon_type": icon.icon_type}]
					):
						icon.insert(ignore_if_duplicate=True)
				except Exception as e:
					dontmanage.error_log(title="Creation of Desktop Icon Failed", message=e)


def create_desktop_icons_from_installed_apps():
	apps = dontmanage.get_installed_apps()
	index = 0
	for a in apps:
		app_title = dontmanage.get_hooks("app_title", app_name=a)[0]
		app_details = dontmanage.get_hooks("add_to_apps_screen", app_name=a)
		if not dontmanage.db.exists("Desktop Icon", [{"icon_type": "App"}, {"app": a}]):
			if len(app_details) != 0:
				icon = dontmanage.new_doc("Desktop Icon")
				icon.label = app_title
				icon.link_type = "External"
				icon.idx = index
				icon.icon_type = "App"
				icon.app = a
				icon.link = app_details[0]["route"]
				icon.logo_url = app_details[0]["logo"]
				if not dontmanage.db.exists("Desktop Icon", [{"label": icon.label, "icon_type": icon.icon_type}]):
					icon.save()
				index += 1


def create_desktop_icons():
	create_desktop_icons_from_installed_apps()
	create_desktop_icons_from_workspace()


def create_user_icons(user, data):
	user_settings = json.loads(data)
	new_icons = user_settings.get("icons_to_create")
	if new_icons:
		new_icons = json.loads(user_settings.get("icons_to_create"))
		if new_icons:
			for icon in new_icons:
				try:
					desktop_icon = dontmanage.new_doc("Desktop Icon")
					desktop_icon.update(icon)
					desktop_icon.owner = user
					desktop_icon.save()
				except Exception as e:
					dontmanage.log_error("Error in syncing icons", e)
			user_settings.pop("icons_to_create", None)
			dontmanage.cache.hset("_user_settings", f"{'Desktop Icon'}::{user}", json.dumps(user_settings))
			return json.dumps(user_settings)
	return data

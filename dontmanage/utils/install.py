# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import getpass

import dontmanage
from dontmanage.email.doctype.notification.notification import install_notification_templates
from dontmanage.geo.doctype.country.country import import_country_and_currency
from dontmanage.utils import cint
from dontmanage.utils.password import update_password


def before_install():
	dontmanage.reload_doc("core", "doctype", "doctype_state")
	dontmanage.reload_doc("core", "doctype", "docfield")
	dontmanage.reload_doc("core", "doctype", "docperm")
	dontmanage.reload_doc("core", "doctype", "doctype_action")
	dontmanage.reload_doc("core", "doctype", "doctype_link")
	dontmanage.reload_doc("desk", "doctype", "form_tour_step")
	dontmanage.reload_doc("desk", "doctype", "form_tour")
	dontmanage.reload_doc("core", "doctype", "doctype")
	dontmanage.clear_cache()


def after_install():
	create_user_type()
	install_basic_docs()

	from dontmanage.core.doctype.file.utils import make_home_folder
	from dontmanage.core.doctype.language.language import sync_languages

	make_home_folder()
	import_country_and_currency()
	sync_languages()

	# save default print setting
	print_settings = dontmanage.get_doc("Print Settings")
	print_settings.save()

	# all roles to admin
	dontmanage.get_doc("User", "Administrator").add_roles(*dontmanage.get_all("Role", pluck="name"))

	# update admin password
	update_password("Administrator", get_admin_password())

	if not dontmanage.conf.skip_setup_wizard:
		# only set home_page if the value doesn't exist in the db
		if not dontmanage.db.get_default("desktop:home_page"):
			dontmanage.db.set_default("desktop:home_page", "setup-wizard")

	# clear test log
	from dontmanage.tests.utils.generators import _clear_test_log

	_clear_test_log()

	add_standard_navbar_items()

	# default templates
	install_notification_templates()

	dontmanage.db.commit()


def create_user_type():
	for user_type in ["System User", "Website User"]:
		if not dontmanage.db.exists("User Type", user_type):
			dontmanage.get_doc({"doctype": "User Type", "name": user_type, "is_standard": 1}).insert(
				ignore_permissions=True
			)


def install_basic_docs():
	# core users / roles
	install_docs = [
		{
			"doctype": "User",
			"name": "Administrator",
			"first_name": "Administrator",
			"email": "admin@example.com",
			"enabled": 1,
			"is_admin": 1,
			"roles": [{"role": "Administrator"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{
			"doctype": "User",
			"name": "Guest",
			"first_name": "Guest",
			"email": "guest@example.com",
			"enabled": 1,
			"is_guest": 1,
			"roles": [{"role": "Guest"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Pending",
			"icon": "question-sign",
			"style": "",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Approved",
			"icon": "ok-sign",
			"style": "Success",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Rejected",
			"icon": "remove",
			"style": "Danger",
		},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Approve"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Reject"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Review"},
	]

	for d in install_docs:
		try:
			dontmanage.get_doc(d).insert(ignore_if_duplicate=True)
		except dontmanage.NameError:
			pass


def get_admin_password():
	return dontmanage.conf.get("admin_password") or getpass.getpass("Set Administrator password: ")


def before_tests():
	if len(dontmanage.get_installed_apps()) > 1:
		# don't run before tests if any other app is installed
		return

	dontmanage.db.truncate("Custom Field")
	dontmanage.db.truncate("Event")

	dontmanage.clear_cache()

	# complete setup if missing
	if not dontmanage.is_setup_complete():
		complete_setup_wizard()

	dontmanage.db.set_single_value("Website Settings", "disable_signup", 0)
	dontmanage.db.commit()
	dontmanage.clear_cache()


def complete_setup_wizard():
	from dontmanage.desk.page.setup_wizard.setup_wizard import setup_complete

	setup_complete(
		{
			"language": "English",
			"email": "test@dontmanageerp.com",
			"full_name": "Test User",
			"password": "test",
			"country": "United States",
			"timezone": "America/New_York",
			"currency": "USD",
			"enable_telemtry": 1,
		}
	)


def add_standard_navbar_items():
	navbar_settings = dontmanage.get_single("Navbar Settings")

	# don't add settings/help options if they're already present
	if navbar_settings.settings_dropdown and navbar_settings.help_dropdown:
		return

	navbar_settings.settings_dropdown = []
	navbar_settings.help_dropdown = []

	for item in dontmanage.get_hooks("standard_navbar_items"):
		navbar_settings.append("settings_dropdown", item)

	for item in dontmanage.get_hooks("standard_help_items"):
		navbar_settings.append("help_dropdown", item)

	navbar_settings.save()


def auto_generate_icons_and_sidebar(app_name=None):
	"""Auto Create desktop icons and workspace sidebars."""
	from dontmanage.desk.doctype.desktop_icon.desktop_icon import create_desktop_icons
	from dontmanage.desk.doctype.workspace_sidebar.workspace_sidebar import (
		create_workspace_sidebar_for_workspaces,
	)

	try:
		print("Creating Workspace Sidebars")
		create_workspace_sidebar_for_workspaces()
		print("Creating Desktop Icons")
		create_desktop_icons()
		# Save the generated icons
		dontmanage.db.commit()  # nosemgrep
		# Save the genreated sidebar links
		dontmanage.db.commit()  # nosemgrep
	except Exception as e:
		print(f"Error creating icons {e}")


def delete_desktop_icon_and_sidebar(app_name, dry_run=False):
	dontmanage.get_hooks(app_name=app_name)
	app_title = dontmanage.get_hooks(app_name=app_name)["app_title"][0]
	icons_to_be_deleted = dontmanage.get_all(
		"Desktop Icon",
		pluck="name",
		or_filters=[
			["Desktop Icon", "name", "=", app_title],
			["Desktop Icon", "parent_icon", "=", app_title],
		],
	)
	print("Deleting Desktop Icons")
	for icon in icons_to_be_deleted:
		dontmanage.delete_doc_if_exists("Desktop Icon", icon)
	# Delete icons
	sidebar_to_be_deleted = dontmanage.get_all("Workspace Sidebar", pluck="name", filters={"app": app_name})
	print("Deleting Workspace Sidebars")
	for icon in sidebar_to_be_deleted:
		dontmanage.delete_doc_if_exists("Workspace Sidebar", icon)

	if dry_run:
		# Delete icons and sidebars
		dontmanage.db.commit()  # nosemgrep

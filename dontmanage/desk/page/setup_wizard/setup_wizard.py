# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage.geo.country_info import get_country_info
from dontmanage.permissions import AUTOMATIC_ROLES
from dontmanage.translate import get_messages_for_boot, send_translations, set_default_language
from dontmanage.utils import cint, now, strip
from dontmanage.utils.password import update_password

from . import install_fixtures


def get_setup_stages(args):  # nosemgrep
	# App setup stage functions should not include dontmanage.db.commit
	# That is done by dontmanage after successful completion of all stages
	stages = [
		{
			"status": "Updating global settings",
			"fail_msg": "Failed to update global settings",
			"tasks": [
				{"fn": update_global_settings, "args": args, "fail_msg": "Failed to update global settings"}
			],
		}
	]

	stages += get_stages_hooks(args) + get_setup_complete_hooks(args)

	stages.append(
		{
			# post executing hooks
			"status": "Wrapping up",
			"fail_msg": "Failed to complete setup",
			"tasks": [{"fn": run_post_setup_complete, "args": args, "fail_msg": "Failed to complete setup"}],
		}
	)

	return stages


@dontmanage.whitelist()
def setup_complete(args):
	"""Calls hooks for `setup_wizard_complete`, sets home page as `desktop`
	and clears cache. If wizard breaks, calls `setup_wizard_exception` hook"""

	# Setup complete: do not throw an exception, let the user continue to desk
	if cint(dontmanage.db.get_single_value("System Settings", "setup_complete")):
		return {"status": "ok"}

	args = parse_args(args)
	stages = get_setup_stages(args)
	is_background_task = dontmanage.conf.get("trigger_site_setup_in_background")

	if is_background_task:
		process_setup_stages.enqueue(stages=stages, user_input=args, is_background_task=True)
		return {"status": "registered"}
	else:
		return process_setup_stages(stages, args)


@dontmanage.task()
def process_setup_stages(stages, user_input, is_background_task=False):
	from dontmanage.utils.telemetry import capture

	capture("initated_server_side", "setup")
	try:
		dontmanage.flags.in_setup_wizard = True
		current_task = None
		for idx, stage in enumerate(stages):
			dontmanage.publish_realtime(
				"setup_task",
				{"progress": [idx, len(stages)], "stage_status": stage.get("status")},
				user=dontmanage.session.user,
			)

			for task in stage.get("tasks"):
				current_task = task
				task.get("fn")(task.get("args"))
	except Exception:
		handle_setup_exception(user_input)
		message = current_task.get("fail_msg") if current_task else "Failed to complete setup"
		dontmanage.log_error(title=f"Setup failed: {message}")
		if not is_background_task:
			dontmanage.response["setup_wizard_failure_message"] = message
			raise
		dontmanage.publish_realtime(
			"setup_task",
			{"status": "fail", "fail_msg": message},
			user=dontmanage.session.user,
		)
	else:
		run_setup_success(user_input)
		capture("completed_server_side", "setup")
		if not is_background_task:
			return {"status": "ok"}
		dontmanage.publish_realtime("setup_task", {"status": "ok"}, user=dontmanage.session.user)
	finally:
		dontmanage.flags.in_setup_wizard = False


def update_global_settings(args):  # nosemgrep
	if args.language and args.language != "English":
		set_default_language(get_language_code(args.lang))
		dontmanage.db.commit()
	dontmanage.clear_cache()

	update_system_settings(args)
	create_or_update_user(args)
	set_timezone(args)


def run_post_setup_complete(args):  # nosemgrep
	disable_future_access()
	dontmanage.db.commit()
	dontmanage.clear_cache()
	# HACK: due to race condition sometimes old doc stays in cache.
	# Remove this when we have reliable cache reset for docs
	dontmanage.get_cached_doc("System Settings") and dontmanage.get_doc("System Settings")


def run_setup_success(args):  # nosemgrep
	for hook in dontmanage.get_hooks("setup_wizard_success"):
		dontmanage.get_attr(hook)(args)
	install_fixtures.install()


def get_stages_hooks(args):  # nosemgrep
	stages = []
	for method in dontmanage.get_hooks("setup_wizard_stages"):
		stages += dontmanage.get_attr(method)(args)
	return stages


def get_setup_complete_hooks(args):  # nosemgrep
	return [
		{
			"status": "Executing method",
			"fail_msg": "Failed to execute method",
			"tasks": [
				{
					"fn": dontmanage.get_attr(method),
					"args": args,
					"fail_msg": "Failed to execute method",
				}
			],
		}
		for method in dontmanage.get_hooks("setup_wizard_complete")
	]


def handle_setup_exception(args):  # nosemgrep
	dontmanage.db.rollback()
	if args:
		traceback = dontmanage.get_traceback(with_context=True)
		print(traceback)
		for hook in dontmanage.get_hooks("setup_wizard_exception"):
			dontmanage.get_attr(hook)(traceback, args)


def update_system_settings(args):  # nosemgrep
	number_format = get_country_info(args.get("country")).get("number_format", "#,###.##")

	# replace these as float number formats, as they have 0 precision
	# and are currency number formats and not for floats
	if number_format == "#.###":
		number_format = "#.###,##"
	elif number_format == "#,###":
		number_format = "#,###.##"

	system_settings = dontmanage.get_doc("System Settings", "System Settings")
	system_settings.update(
		{
			"country": args.get("country"),
			"language": get_language_code(args.get("language")) or "en",
			"time_zone": args.get("timezone"),
			"float_precision": 3,
			"rounding_method": "Banker's Rounding",
			"date_format": dontmanage.db.get_value("Country", args.get("country"), "date_format"),
			"time_format": dontmanage.db.get_value("Country", args.get("country"), "time_format"),
			"number_format": number_format,
			"enable_scheduler": 1 if not dontmanage.flags.in_test else 0,
			"backup_limit": 3,  # Default for downloadable backups
			"enable_telemetry": cint(args.get("enable_telemetry")),
		}
	)
	system_settings.save()
	if args.get("allow_recording_first_session"):
		dontmanage.db.set_default("session_recording_start", now())


def create_or_update_user(args):  # nosemgrep
	email = args.get("email")
	if not email:
		return

	first_name, last_name = args.get("full_name", ""), ""
	if " " in first_name:
		first_name, last_name = first_name.split(" ", 1)

	if user := dontmanage.db.get_value("User", email, ["first_name", "last_name"], as_dict=True):
		if user.first_name != first_name or user.last_name != last_name:
			(
				dontmanage.qb.update("User")
				.set("first_name", first_name)
				.set("last_name", last_name)
				.set("full_name", args.get("full_name"))
			).run()
	else:
		_mute_emails, dontmanage.flags.mute_emails = dontmanage.flags.mute_emails, True

		user = dontmanage.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
			}
		)
		user.append_roles(*_get_default_roles())
		user.flags.no_welcome_mail = True
		user.insert()

		dontmanage.flags.mute_emails = _mute_emails

	if args.get("password"):
		update_password(email, args.get("password"))


def set_timezone(args):  # nosemgrep
	if args.get("timezone"):
		for name in dontmanage.STANDARD_USERS:
			dontmanage.db.set_value("User", name, "time_zone", args.get("timezone"))


def parse_args(args):  # nosemgrep
	if not args:
		args = dontmanage.local.form_dict
	if isinstance(args, str):
		args = json.loads(args)

	args = dontmanage._dict(args)

	# strip the whitespace
	for key, value in args.items():
		if isinstance(value, str):
			args[key] = strip(value)

	return args


def add_all_roles_to(name):
	user = dontmanage.get_doc("User", name)
	user.append_roles(*_get_default_roles())
	user.save()


def _get_default_roles() -> set[str]:
	skip_roles = {
		"Administrator",
		"Customer",
		"Supplier",
		"Partner",
		"Employee",
	}.union(AUTOMATIC_ROLES)
	return set(dontmanage.get_all("Role", pluck="name")) - skip_roles


def disable_future_access():
	dontmanage.db.set_default("desktop:home_page", "workspace")
	# Enable onboarding after install
	dontmanage.db.set_single_value("System Settings", "enable_onboarding", 1)

	dontmanage.db.set_single_value("System Settings", "setup_complete", 1)


@dontmanage.whitelist()
def load_messages(language):
	"""Load translation messages for given language from all `setup_wizard_requires`
	javascript files"""
	dontmanage.clear_cache()
	set_default_language(get_language_code(language))
	dontmanage.db.commit()
	send_translations(get_messages_for_boot())
	return dontmanage.local.lang


@dontmanage.whitelist()
def load_languages():
	language_codes = dontmanage.db.sql(
		"select language_code, language_name from tabLanguage order by name", as_dict=True
	)
	codes_to_names = {}
	for d in language_codes:
		codes_to_names[d.language_code] = d.language_name
	return {
		"default_language": dontmanage.db.get_value("Language", dontmanage.local.lang, "language_name")
		or dontmanage.local.lang,
		"languages": sorted(dontmanage.db.sql_list("select language_name from tabLanguage order by name")),
		"codes_to_names": codes_to_names,
	}


@dontmanage.whitelist()
def load_country():
	from dontmanage.sessions import get_geo_ip_country

	return get_geo_ip_country(dontmanage.local.request_ip) if dontmanage.local.request_ip else None


@dontmanage.whitelist()
def load_user_details():
	return {
		"full_name": dontmanage.cache.hget("full_name", "signup"),
		"email": dontmanage.cache.hget("email", "signup"),
	}


def prettify_args(args):  # nosemgrep
	# remove attachments
	for key, val in args.items():
		if isinstance(val, str) and "data:image" in val:
			filename = val.split("data:image", 1)[0].strip(", ")
			size = round((len(val) * 3 / 4) / 1048576.0, 2)
			args[key] = f"Image Attached: '{filename}' of size {size} MB"

	pretty_args = []
	pretty_args.extend(f"{key} = {args[key]}" for key in sorted(args))
	return pretty_args


def email_setup_wizard_exception(traceback, args):  # nosemgrep
	if not dontmanage.conf.setup_wizard_exception_email:
		return

	pretty_args = prettify_args(args)
	message = """

#### Traceback

<pre>{traceback}</pre>

---

#### Setup Wizard Arguments

<pre>{args}</pre>

---

#### Request Headers

<pre>{headers}</pre>

---

#### Basic Information

- **Site:** {site}
- **User:** {user}""".format(
		site=dontmanage.local.site,
		traceback=traceback,
		args="\n".join(pretty_args),
		user=dontmanage.session.user,
		headers=dontmanage.request.headers if dontmanage.request else "[no request]",
	)

	dontmanage.sendmail(
		recipients=dontmanage.conf.setup_wizard_exception_email,
		sender=dontmanage.session.user,
		subject=f"Setup failed: {dontmanage.local.site}",
		message=message,
		delayed=False,
	)


def log_setup_wizard_exception(traceback, args):  # nosemgrep
	with open("../logs/setup-wizard.log", "w+") as setup_log:
		setup_log.write(traceback)
		setup_log.write(json.dumps(args))


def get_language_code(lang):
	return dontmanage.db.get_value("Language", {"language_name": lang})


def enable_twofactor_all_roles():
	all_role = dontmanage.get_doc("Role", {"role_name": "All"})
	all_role.two_factor_auth = True
	all_role.save(ignore_permissions=True)


def make_records(records, debug=False):
	from dontmanage import _dict
	from dontmanage.modules import scrub

	if debug:
		print("make_records: in DEBUG mode")

	# LOG every success and failure
	for record in records:
		doctype = record.get("doctype")
		condition = record.get("__condition")

		if condition and not condition():
			continue

		doc = dontmanage.new_doc(doctype)
		doc.update(record)

		# ignore mandatory for root
		parent_link_field = "parent_" + scrub(doc.doctype)
		if doc.meta.get_field(parent_link_field) and not doc.get(parent_link_field):
			doc.flags.ignore_mandatory = True

		savepoint = "setup_fixtures_creation"
		try:
			dontmanage.db.savepoint(savepoint)
			doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
		except Exception as e:
			dontmanage.clear_last_message()
			dontmanage.db.rollback(save_point=savepoint)
			exception = record.get("__exception")
			if exception:
				config = _dict(exception)
				if isinstance(e, config.exception):
					config.handler()
				else:
					show_document_insert_error()
			else:
				show_document_insert_error()


def show_document_insert_error():
	print("Document Insert Error")
	print(dontmanage.get_traceback())
	dontmanage.log_error("Exception during Setup")

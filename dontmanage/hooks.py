from . import __version__ as app_version

app_name = "dontmanage"
app_title = "DontManage Framework"
app_publisher = "DontManage Technologies"
app_description = "Full stack web framework with Python, Javascript, MariaDB, Redis, Node"
source_link = "https://github.com/dontmanage/dontmanage"
app_license = "MIT"
app_logo_url = "/assets/dontmanage/images/dontmanage-framework-logo.svg"

develop_version = "14.x.x-develop"

app_email = "developers@dontmanage.io"

docs_app = "dontmanage_docs"

translator_url = "https://translate.dontmanageerp.com"

before_install = "dontmanage.utils.install.before_install"
after_install = "dontmanage.utils.install.after_install"

page_js = {"setup-wizard": "public/js/dontmanage/setup_wizard.js"}

# website
app_include_js = [
	"libs.bundle.js",
	"desk.bundle.js",
	"list.bundle.js",
	"form.bundle.js",
	"controls.bundle.js",
	"report.bundle.js",
]
app_include_css = [
	"desk.bundle.css",
	"report.bundle.css",
]

doctype_js = {
	"Web Page": "public/js/dontmanage/utils/web_template.js",
	"Website Settings": "public/js/dontmanage/utils/web_template.js",
}

web_include_js = ["website_script.js"]

web_include_css = []

email_css = ["email.bundle.css"]

website_route_rules = [
	{"from_route": "/blog/<category>", "to_route": "Blog Post"},
	{"from_route": "/kb/<category>", "to_route": "Help Article"},
	{"from_route": "/newsletters", "to_route": "Newsletter"},
	{"from_route": "/profile", "to_route": "me"},
	{"from_route": "/app/<path:app_path>", "to_route": "app"},
]

website_redirects = [
	{"source": r"/desk(.*)", "target": r"/app\1"},
]

base_template = "templates/base.html"

write_file_keys = ["file_url", "file_name"]

notification_config = "dontmanage.core.notifications.get_notification_config"

before_tests = "dontmanage.utils.install.before_tests"

email_append_to = ["Event", "ToDo", "Communication"]

calendars = ["Event"]

leaderboards = "dontmanage.desk.leaderboard.get_leaderboards"

# login

on_session_creation = [
	"dontmanage.core.doctype.activity_log.feed.login_feed",
	"dontmanage.core.doctype.user.user.notify_admin_access_to_system_manager",
]

on_logout = (
	"dontmanage.core.doctype.session_default_settings.session_default_settings.clear_session_defaults"
)

# permissions

permission_query_conditions = {
	"Event": "dontmanage.desk.doctype.event.event.get_permission_query_conditions",
	"ToDo": "dontmanage.desk.doctype.todo.todo.get_permission_query_conditions",
	"User": "dontmanage.core.doctype.user.user.get_permission_query_conditions",
	"Dashboard Settings": "dontmanage.desk.doctype.dashboard_settings.dashboard_settings.get_permission_query_conditions",
	"Notification Log": "dontmanage.desk.doctype.notification_log.notification_log.get_permission_query_conditions",
	"Dashboard": "dontmanage.desk.doctype.dashboard.dashboard.get_permission_query_conditions",
	"Dashboard Chart": "dontmanage.desk.doctype.dashboard_chart.dashboard_chart.get_permission_query_conditions",
	"Number Card": "dontmanage.desk.doctype.number_card.number_card.get_permission_query_conditions",
	"Notification Settings": "dontmanage.desk.doctype.notification_settings.notification_settings.get_permission_query_conditions",
	"Note": "dontmanage.desk.doctype.note.note.get_permission_query_conditions",
	"Kanban Board": "dontmanage.desk.doctype.kanban_board.kanban_board.get_permission_query_conditions",
	"Contact": "dontmanage.contacts.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "dontmanage.contacts.address_and_contact.get_permission_query_conditions_for_address",
	"Communication": "dontmanage.core.doctype.communication.communication.get_permission_query_conditions_for_communication",
	"Workflow Action": "dontmanage.workflow.doctype.workflow_action.workflow_action.get_permission_query_conditions",
	"Prepared Report": "dontmanage.core.doctype.prepared_report.prepared_report.get_permission_query_condition",
}

has_permission = {
	"Event": "dontmanage.desk.doctype.event.event.has_permission",
	"ToDo": "dontmanage.desk.doctype.todo.todo.has_permission",
	"User": "dontmanage.core.doctype.user.user.has_permission",
	"Note": "dontmanage.desk.doctype.note.note.has_permission",
	"Dashboard Chart": "dontmanage.desk.doctype.dashboard_chart.dashboard_chart.has_permission",
	"Number Card": "dontmanage.desk.doctype.number_card.number_card.has_permission",
	"Kanban Board": "dontmanage.desk.doctype.kanban_board.kanban_board.has_permission",
	"Contact": "dontmanage.contacts.address_and_contact.has_permission",
	"Address": "dontmanage.contacts.address_and_contact.has_permission",
	"Communication": "dontmanage.core.doctype.communication.communication.has_permission",
	"Workflow Action": "dontmanage.workflow.doctype.workflow_action.workflow_action.has_permission",
	"File": "dontmanage.core.doctype.file.file.has_permission",
	"Prepared Report": "dontmanage.core.doctype.prepared_report.prepared_report.has_permission",
}

has_website_permission = {
	"Address": "dontmanage.contacts.doctype.address.address.has_website_permission"
}

jinja = {
	"methods": "dontmanage.utils.jinja_globals",
	"filters": [
		"dontmanage.utils.data.global_date_format",
		"dontmanage.utils.markdown",
		"dontmanage.website.utils.get_shade",
		"dontmanage.website.utils.abs_url",
	],
}

standard_queries = {"User": "dontmanage.core.doctype.user.user.user_query"}

doc_events = {
	"*": {
		"after_insert": [
			"dontmanage.event_streaming.doctype.event_update_log.event_update_log.notify_consumers"
		],
		"on_update": [
			"dontmanage.desk.notifications.clear_doctype_notifications",
			"dontmanage.core.doctype.activity_log.feed.update_feed",
			"dontmanage.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"dontmanage.automation.doctype.assignment_rule.assignment_rule.apply",
			"dontmanage.core.doctype.file.utils.attach_files_to_document",
			"dontmanage.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
			"dontmanage.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"dontmanage.core.doctype.user_type.user_type.apply_permissions_for_non_standard_user_type",
		],
		"after_rename": "dontmanage.desk.notifications.clear_doctype_notifications",
		"on_cancel": [
			"dontmanage.desk.notifications.clear_doctype_notifications",
			"dontmanage.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"dontmanage.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
		],
		"on_trash": [
			"dontmanage.desk.notifications.clear_doctype_notifications",
			"dontmanage.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"dontmanage.event_streaming.doctype.event_update_log.event_update_log.notify_consumers",
		],
		"on_update_after_submit": [
			"dontmanage.workflow.doctype.workflow_action.workflow_action.process_workflow_actions"
		],
		"on_change": [
			"dontmanage.social.doctype.energy_point_rule.energy_point_rule.process_energy_points",
			"dontmanage.automation.doctype.milestone_tracker.milestone_tracker.evaluate_milestone",
		],
	},
	"Event": {
		"after_insert": "dontmanage.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar",
		"on_update": "dontmanage.integrations.doctype.google_calendar.google_calendar.update_event_in_google_calendar",
		"on_trash": "dontmanage.integrations.doctype.google_calendar.google_calendar.delete_event_from_google_calendar",
	},
	"Contact": {
		"after_insert": "dontmanage.integrations.doctype.google_contacts.google_contacts.insert_contacts_to_google_contacts",
		"on_update": "dontmanage.integrations.doctype.google_contacts.google_contacts.update_contacts_to_google_contacts",
	},
	"DocType": {
		"on_update": "dontmanage.cache_manager.build_domain_restriced_doctype_cache",
	},
	"Page": {
		"on_update": "dontmanage.cache_manager.build_domain_restriced_page_cache",
	},
}

scheduler_events = {
	"cron": {
		"0/15 * * * *": [
			"dontmanage.oauth.delete_oauth2_data",
			"dontmanage.website.doctype.web_page.web_page.check_publish_status",
			"dontmanage.twofactor.delete_all_barcodes_for_users",
		]
	},
	"all": [
		"dontmanage.email.queue.flush",
		"dontmanage.email.doctype.email_account.email_account.pull",
		"dontmanage.email.doctype.email_account.email_account.notify_unreplied",
		"dontmanage.utils.global_search.sync_global_search",
		"dontmanage.monitor.flush",
	],
	"hourly": [
		"dontmanage.model.utils.link_count.update_link_count",
		"dontmanage.model.utils.user_settings.sync_user_settings",
		"dontmanage.utils.error.collect_error_snapshots",
		"dontmanage.desk.page.backups.backups.delete_downloadable_backups",
		"dontmanage.deferred_insert.save_to_db",
		"dontmanage.desk.form.document_follow.send_hourly_updates",
		"dontmanage.integrations.doctype.google_calendar.google_calendar.sync",
		"dontmanage.email.doctype.newsletter.newsletter.send_scheduled_email",
		"dontmanage.website.doctype.personal_data_deletion_request.personal_data_deletion_request.process_data_deletion_request",
	],
	"daily": [
		"dontmanage.email.queue.set_expiry_for_email_queue",
		"dontmanage.desk.notifications.clear_notifications",
		"dontmanage.desk.doctype.event.event.send_event_digest",
		"dontmanage.sessions.clear_expired_sessions",
		"dontmanage.email.doctype.notification.notification.trigger_daily_alerts",
		"dontmanage.website.doctype.personal_data_deletion_request.personal_data_deletion_request.remove_unverified_record",
		"dontmanage.desk.form.document_follow.send_daily_updates",
		"dontmanage.social.doctype.energy_point_settings.energy_point_settings.allocate_review_points",
		"dontmanage.integrations.doctype.google_contacts.google_contacts.sync",
		"dontmanage.automation.doctype.auto_repeat.auto_repeat.make_auto_repeat_entry",
		"dontmanage.automation.doctype.auto_repeat.auto_repeat.set_auto_repeat_as_completed",
		"dontmanage.email.doctype.unhandled_email.unhandled_email.remove_old_unhandled_emails",
		"dontmanage.core.doctype.prepared_report.prepared_report.delete_expired_prepared_reports",
		"dontmanage.core.doctype.log_settings.log_settings.run_log_clean_up",
	],
	"daily_long": [
		"dontmanage.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_daily",
		"dontmanage.utils.change_log.check_for_update",
		"dontmanage.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_daily",
		"dontmanage.email.doctype.auto_email_report.auto_email_report.send_daily",
		"dontmanage.integrations.doctype.google_drive.google_drive.daily_backup",
	],
	"weekly_long": [
		"dontmanage.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_weekly",
		"dontmanage.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_weekly",
		"dontmanage.desk.form.document_follow.send_weekly_updates",
		"dontmanage.social.doctype.energy_point_log.energy_point_log.send_weekly_summary",
		"dontmanage.integrations.doctype.google_drive.google_drive.weekly_backup",
	],
	"monthly": [
		"dontmanage.email.doctype.auto_email_report.auto_email_report.send_monthly",
		"dontmanage.social.doctype.energy_point_log.energy_point_log.send_monthly_summary",
	],
	"monthly_long": [
		"dontmanage.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_monthly"
	],
}

get_translated_dict = {
	("doctype", "System Settings"): "dontmanage.geo.country_info.get_translated_dict",
	("page", "setup-wizard"): "dontmanage.geo.country_info.get_translated_dict",
}

sounds = [
	{"name": "email", "src": "/assets/dontmanage/sounds/email.mp3", "volume": 0.1},
	{"name": "submit", "src": "/assets/dontmanage/sounds/submit.mp3", "volume": 0.1},
	{"name": "cancel", "src": "/assets/dontmanage/sounds/cancel.mp3", "volume": 0.1},
	{"name": "delete", "src": "/assets/dontmanage/sounds/delete.mp3", "volume": 0.05},
	{"name": "click", "src": "/assets/dontmanage/sounds/click.mp3", "volume": 0.05},
	{"name": "error", "src": "/assets/dontmanage/sounds/error.mp3", "volume": 0.1},
	{"name": "alert", "src": "/assets/dontmanage/sounds/alert.mp3", "volume": 0.2},
	# {"name": "chime", "src": "/assets/dontmanage/sounds/chime.mp3"},
]

setup_wizard_exception = [
	"dontmanage.desk.page.setup_wizard.setup_wizard.email_setup_wizard_exception",
	"dontmanage.desk.page.setup_wizard.setup_wizard.log_setup_wizard_exception",
]

before_migrate = []
after_migrate = ["dontmanage.website.doctype.website_theme.website_theme.after_migrate"]

otp_methods = ["OTP App", "Email", "SMS"]

user_data_fields = [
	{"doctype": "Access Log", "strict": True},
	{"doctype": "Activity Log", "strict": True},
	{"doctype": "Comment", "strict": True},
	{
		"doctype": "Contact",
		"filter_by": "email_id",
		"redact_fields": ["first_name", "last_name", "phone", "mobile_no"],
		"rename": True,
	},
	{"doctype": "Contact Email", "filter_by": "email_id"},
	{
		"doctype": "Address",
		"filter_by": "email_id",
		"redact_fields": [
			"address_title",
			"address_line1",
			"address_line2",
			"city",
			"county",
			"state",
			"pincode",
			"phone",
			"fax",
		],
	},
	{
		"doctype": "Communication",
		"filter_by": "sender",
		"redact_fields": ["sender_full_name", "phone_no", "content"],
	},
	{"doctype": "Communication", "filter_by": "recipients"},
	{"doctype": "Email Group Member", "filter_by": "email"},
	{"doctype": "Email Unsubscribe", "filter_by": "email", "partial": True},
	{"doctype": "Email Queue", "filter_by": "sender"},
	{"doctype": "Email Queue Recipient", "filter_by": "recipient"},
	{
		"doctype": "File",
		"filter_by": "attached_to_name",
		"redact_fields": ["file_name", "file_url"],
	},
	{
		"doctype": "User",
		"filter_by": "name",
		"redact_fields": [
			"email",
			"username",
			"first_name",
			"middle_name",
			"last_name",
			"full_name",
			"birth_date",
			"user_image",
			"phone",
			"mobile_no",
			"location",
			"banner_image",
			"interest",
			"bio",
			"email_signature",
		],
	},
	{"doctype": "Version", "strict": True},
]

global_search_doctypes = {
	"Default": [
		{"doctype": "Contact"},
		{"doctype": "Address"},
		{"doctype": "ToDo"},
		{"doctype": "Note"},
		{"doctype": "Event"},
		{"doctype": "Blog Post"},
		{"doctype": "Dashboard"},
		{"doctype": "Country"},
		{"doctype": "Currency"},
		{"doctype": "Newsletter"},
		{"doctype": "Letter Head"},
		{"doctype": "Workflow"},
		{"doctype": "Web Page"},
		{"doctype": "Web Form"},
	]
}

override_whitelisted_methods = {
	# Legacy File APIs
	"dontmanage.core.doctype.file.file.download_file": "download_file",
	"dontmanage.core.doctype.file.file.unzip_file": "dontmanage.core.api.file.unzip_file",
	"dontmanage.core.doctype.file.file.get_attached_images": "dontmanage.core.api.file.get_attached_images",
	"dontmanage.core.doctype.file.file.get_files_in_folder": "dontmanage.core.api.file.get_files_in_folder",
	"dontmanage.core.doctype.file.file.get_files_by_search_text": "dontmanage.core.api.file.get_files_by_search_text",
	"dontmanage.core.doctype.file.file.get_max_file_size": "dontmanage.core.api.file.get_max_file_size",
	"dontmanage.core.doctype.file.file.create_new_folder": "dontmanage.core.api.file.create_new_folder",
	"dontmanage.core.doctype.file.file.move_file": "dontmanage.core.api.file.move_file",
	"dontmanage.core.doctype.file.file.zip_files": "dontmanage.core.api.file.zip_files",
	# Legacy (& Consistency) OAuth2 APIs
	"dontmanage.www.login.login_via_google": "dontmanage.integrations.oauth2_logins.login_via_google",
	"dontmanage.www.login.login_via_github": "dontmanage.integrations.oauth2_logins.login_via_github",
	"dontmanage.www.login.login_via_facebook": "dontmanage.integrations.oauth2_logins.login_via_facebook",
	"dontmanage.www.login.login_via_dontmanage": "dontmanage.integrations.oauth2_logins.login_via_dontmanage",
	"dontmanage.www.login.login_via_office365": "dontmanage.integrations.oauth2_logins.login_via_office365",
	"dontmanage.www.login.login_via_salesforce": "dontmanage.integrations.oauth2_logins.login_via_salesforce",
	"dontmanage.www.login.login_via_fairlogin": "dontmanage.integrations.oauth2_logins.login_via_fairlogin",
}

ignore_links_on_delete = [
	"Communication",
	"ToDo",
	"DocShare",
	"Email Unsubscribe",
	"Activity Log",
	"File",
	"Version",
	"Document Follow",
	"Comment",
	"View Log",
	"Tag Link",
	"Notification Log",
	"Email Queue",
	"Document Share Key",
	"Integration Request",
	"Unhandled Email",
	"Webhook Request Log",
]

# Request Hooks
before_request = [
	"dontmanage.recorder.record",
	"dontmanage.monitor.start",
	"dontmanage.rate_limiter.apply",
]
after_request = ["dontmanage.rate_limiter.update", "dontmanage.monitor.stop", "dontmanage.recorder.dump"]

# Background Job Hooks
before_job = [
	"dontmanage.monitor.start",
]
after_job = [
	"dontmanage.monitor.stop",
	"dontmanage.utils.file_lock.release_document_locks",
]

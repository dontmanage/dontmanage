# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import os
from urllib.parse import quote

from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

import dontmanage
from dontmanage import _
from dontmanage.integrations.google_oauth import GoogleOAuth
from dontmanage.integrations.offsite_backup_utils import (
	get_latest_backup_file,
	send_email,
	validate_file_size,
)
from dontmanage.model.document import Document
from dontmanage.utils import get_backups_path, get_bench_path
from dontmanage.utils.background_jobs import enqueue
from dontmanage.utils.backups import new_backup


class GoogleDrive(Document):
	def validate(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.backup_folder_name != self.backup_folder_name:
			self.backup_folder_id = ""

	def get_access_token(self):
		if not self.refresh_token:
			button_label = dontmanage.bold(_("Allow Google Drive Access"))
			raise dontmanage.ValidationError(_("Click on {0} to generate Refresh Token.").format(button_label))

		oauth_obj = GoogleOAuth("drive")
		r = oauth_obj.refresh_access_token(
			self.get_password(fieldname="refresh_token", raise_exception=False)
		)

		return r.get("access_token")


@dontmanage.whitelist(methods=["POST"])
def authorize_access(reauthorize=False, code=None):
	"""
	If no Authorization code get it from Google and then request for Refresh Token.
	Google Contact Name is set to flags to set_value after Authorization Code is obtained.
	"""

	oauth_code = (
		dontmanage.db.get_single_value("Google Drive", "authorization_code") if not code else code
	)
	oauth_obj = GoogleOAuth("drive")

	if not oauth_code or reauthorize:
		if reauthorize:
			dontmanage.db.set_single_value("Google Drive", "backup_folder_id", "")
		return oauth_obj.get_authentication_url(
			{
				"redirect": f"/app/Form/{quote('Google Drive')}",
			},
		)

	r = oauth_obj.authorize(oauth_code)
	dontmanage.db.set_single_value(
		"Google Drive",
		{"authorization_code": oauth_code, "refresh_token": r.get("refresh_token")},
	)


def get_google_drive_object():
	"""
	Returns an object of Google Drive.
	"""
	account = dontmanage.get_doc("Google Drive")
	oauth_obj = GoogleOAuth("drive")

	google_drive = oauth_obj.get_google_service_object(
		account.get_access_token(),
		account.get_password(fieldname="indexing_refresh_token", raise_exception=False),
	)

	return google_drive, account


def check_for_folder_in_google_drive():
	"""Checks if folder exists in Google Drive else create it."""

	def _create_folder_in_google_drive(google_drive, account):
		file_metadata = {
			"name": account.backup_folder_name,
			"mimeType": "application/vnd.google-apps.folder",
		}

		try:
			folder = google_drive.files().create(body=file_metadata, fields="id").execute()
			dontmanage.db.set_single_value("Google Drive", "backup_folder_id", folder.get("id"))
			dontmanage.db.commit()
		except HttpError as e:
			dontmanage.throw(
				_("Google Drive - Could not create folder in Google Drive - Error Code {0}").format(e)
			)

	google_drive, account = get_google_drive_object()

	if account.backup_folder_id:
		return

	backup_folder_exists = False

	try:
		google_drive_folders = (
			google_drive.files().list(q="mimeType='application/vnd.google-apps.folder'").execute()
		)
	except HttpError as e:
		dontmanage.throw(
			_("Google Drive - Could not find folder in Google Drive - Error Code {0}").format(e)
		)

	for f in google_drive_folders.get("files"):
		if f.get("name") == account.backup_folder_name:
			dontmanage.db.set_single_value("Google Drive", "backup_folder_id", f.get("id"))
			dontmanage.db.commit()
			backup_folder_exists = True
			break

	if not backup_folder_exists:
		_create_folder_in_google_drive(google_drive, account)


@dontmanage.whitelist()
def take_backup():
	"""Enqueue longjob for taking backup to Google Drive"""
	enqueue(
		"dontmanage.integrations.doctype.google_drive.google_drive.upload_system_backup_to_google_drive",
		queue="long",
		timeout=1500,
	)
	dontmanage.msgprint(_("Queued for backup. It may take a few minutes to an hour."))


def upload_system_backup_to_google_drive():
	"""
	Upload system backup to Google Drive
	"""
	# Get Google Drive Object
	google_drive, account = get_google_drive_object()

	# Check if folder exists in Google Drive
	check_for_folder_in_google_drive()
	account.load_from_db()

	validate_file_size()

	if dontmanage.flags.create_new_backup:
		set_progress(1, "Backing up Data.")
		backup = new_backup()
		file_urls = []
		file_urls.append(backup.backup_path_db)
		file_urls.append(backup.backup_path_conf)

		if account.file_backup:
			file_urls.append(backup.backup_path_files)
			file_urls.append(backup.backup_path_private_files)
	else:
		file_urls = get_latest_backup_file(with_files=account.file_backup)

	for fileurl in file_urls:
		if not fileurl:
			continue

		file_metadata = {"name": os.path.basename(fileurl), "parents": [account.backup_folder_id]}

		try:
			media = MediaFileUpload(
				get_absolute_path(filename=fileurl), mimetype="application/gzip", resumable=True
			)
		except OSError as e:
			dontmanage.throw(_("Google Drive - Could not locate - {0}").format(e))

		try:
			set_progress(2, "Uploading backup to Google Drive.")
			google_drive.files().create(body=file_metadata, media_body=media, fields="id").execute()
		except HttpError as e:
			send_email(False, "Google Drive", "Google Drive", "email", error_status=e)

	set_progress(3, "Uploading successful.")
	dontmanage.db.set_single_value("Google Drive", "last_backup_on", dontmanage.utils.now_datetime())
	send_email(True, "Google Drive", "Google Drive", "email")
	return _("Google Drive Backup Successful.")


def daily_backup():
	drive_settings = dontmanage.db.get_singles_dict("Google Drive", cast=True)
	if drive_settings.enable and drive_settings.frequency == "Daily":
		upload_system_backup_to_google_drive()


def weekly_backup():
	drive_settings = dontmanage.db.get_singles_dict("Google Drive", cast=True)
	if drive_settings.enable and drive_settings.frequency == "Weekly":
		upload_system_backup_to_google_drive()


def get_absolute_path(filename):
	file_path = os.path.join(get_backups_path()[2:], os.path.basename(filename))
	return f"{get_bench_path()}/sites/{file_path}"


def set_progress(progress, message):
	dontmanage.publish_realtime(
		"upload_to_google_drive",
		dict(progress=progress, total=3, message=message),
		user=dontmanage.session.user,
	)

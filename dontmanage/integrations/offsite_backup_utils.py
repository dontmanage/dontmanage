# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import glob
import os

import dontmanage
from dontmanage.utils import cint, split_emails


def send_email(success, service_name, doctype, email_field, error_status=None):
	recipients = get_recipients(doctype, email_field)
	if not recipients:
		dontmanage.log_error(
			f"No Email Recipient found for {service_name}",
			f"{service_name}: Failed to send backup status email",
		)
		return

	if success:
		if not dontmanage.db.get_single_value(doctype, "send_email_for_successful_backup"):
			return

		subject = "Backup Upload Successful"
		message = """
<h3>Backup Uploaded Successfully!</h3>
<p>Hi there, this is just to inform you that your backup was successfully uploaded to your {} bucket. So relax!</p>""".format(
			service_name
		)
	else:
		subject = "[Warning] Backup Upload Failed"
		message = f"""
<h3>Backup Upload Failed!</h3>
<p>Oops, your automated backup to {service_name} failed.</p>
<p>Error message: {error_status}</p>
<p>Please contact your system manager for more information.</p>"""

	dontmanage.sendmail(recipients=recipients, subject=subject, message=message)


def get_recipients(doctype, email_field):
	if not dontmanage.db:
		dontmanage.connect()

	return split_emails(dontmanage.db.get_value(doctype, None, email_field))


def get_latest_backup_file(with_files=False):
	from dontmanage.utils.backups import BackupGenerator

	odb = BackupGenerator(
		dontmanage.conf.db_name,
		dontmanage.conf.db_name,
		dontmanage.conf.db_password,
		db_host=dontmanage.conf.db_host,
		db_port=dontmanage.conf.db_port,
		db_type=dontmanage.conf.db_type,
	)
	database, public, private, config = odb.get_recent_backup(older_than=24 * 30)

	if with_files:
		return database, config, public, private

	return database, config


def get_file_size(file_path, unit="MB"):
	file_size = os.path.getsize(file_path)

	memory_size_unit_mapper = {"KB": 1, "MB": 2, "GB": 3, "TB": 4}
	i = 0
	while i < memory_size_unit_mapper[unit]:
		file_size = file_size / 1000.0
		i += 1

	return file_size


def get_chunk_site(file_size):
	"""this function will return chunk size in megabytes based on file size"""

	file_size_in_gb = cint(file_size / 1024 / 1024)

	MB = 1024 * 1024
	if file_size_in_gb > 5000:
		return 200 * MB
	elif file_size_in_gb >= 3000:
		return 150 * MB
	elif file_size_in_gb >= 1000:
		return 100 * MB
	elif file_size_in_gb >= 500:
		return 50 * MB
	else:
		return 15 * MB


def validate_file_size():
	dontmanage.flags.create_new_backup = True
	latest_file, site_config = get_latest_backup_file()
	file_size = get_file_size(latest_file, unit="GB") if latest_file else 0

	if file_size > 1:
		dontmanage.flags.create_new_backup = False


def generate_files_backup():
	from dontmanage.utils.backups import BackupGenerator

	backup = BackupGenerator(
		dontmanage.conf.db_name,
		dontmanage.conf.db_name,
		dontmanage.conf.db_password,
		db_host=dontmanage.conf.db_host,
		db_port=dontmanage.conf.db_port,
		db_type=dontmanage.conf.db_type,
	)

	backup.set_backup_file_name()
	backup.zip_files()

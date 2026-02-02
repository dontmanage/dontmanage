# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
from datetime import timedelta

import dontmanage
from dontmanage.core.doctype.scheduled_job_type.scheduled_job_type import sync_jobs
from dontmanage.tests import IntegrationTestCase
from dontmanage.utils import get_datetime
from dontmanage.utils.data import add_to_date, now_datetime


class TestScheduledJobType(IntegrationTestCase):
	def setUp(self):
		dontmanage.db.rollback()
		dontmanage.db.truncate("Scheduled Job Type")
		sync_jobs()
		dontmanage.db.commit()

	def test_throws_on_duplicate_job(self):
		job_config = dict(
			doctype="Scheduled Job Type",
			method="dontmanage.desk.notifications.clear_notifications",
			frequency="Weekly",
		)
		dontmanage.get_doc(job_config).insert()

		duplicate_job = dontmanage.get_doc(job_config)

		self.assertRaises(Exception, duplicate_job.insert)
		dontmanage.db.rollback()

	def test_throws_on_duplicate_job_with_cron_format(self):
		job_config = dict(
			doctype="Scheduled Job Type",
			method="dontmanage.desk.notifications.clear_notifications",
			frequency="Cron",
			cron_format="*/1 * * * *",
		)
		dontmanage.get_doc(job_config).insert()

		duplicate_job = dontmanage.get_doc(job_config)

		self.assertRaises(Exception, duplicate_job.insert)
		dontmanage.db.rollback()

	def test_sync_jobs(self):
		all_job = dontmanage.get_doc("Scheduled Job Type", dict(method="dontmanage.email.queue.flush"))
		self.assertEqual(all_job.frequency, "All")

		daily_job = dontmanage.get_doc(
			"Scheduled Job Type", dict(method="dontmanage.desk.notifications.clear_notifications")
		)
		self.assertEqual(daily_job.frequency, "Daily Maintenance")

		# check if cron jobs are synced
		cron_job = dontmanage.get_doc("Scheduled Job Type", dict(method="dontmanage.deferred_insert.save_to_db"))
		self.assertEqual(cron_job.frequency, "Cron")
		self.assertEqual(cron_job.cron_format, "0/15 * * * *")

		# check if jobs are synced after change in hooks
		updated_scheduler_events = {"hourly": ["dontmanage.email.queue.flush"]}
		sync_jobs(updated_scheduler_events)
		updated_scheduled_job = dontmanage.get_doc("Scheduled Job Type", {"method": "dontmanage.email.queue.flush"})
		self.assertEqual(updated_scheduled_job.frequency, "Hourly")

	def test_daily_job(self):
		job = dontmanage.get_doc(
			"Scheduled Job Type",
			dict(method="dontmanage.email.doctype.notification.notification.trigger_daily_alerts"),
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-01-02 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 23:59:59")))

	def test_weekly_job(self):
		job = dontmanage.get_doc(
			"Scheduled Job Type",
			dict(method="dontmanage.desk.form.document_follow.send_weekly_updates"),
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-01-06 00:10:01")))  # +10 min because of jitter
		self.assertFalse(job.is_event_due(get_datetime("2019-01-02 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-05 23:59:59")))

	def test_monthly_job(self):
		job = dontmanage.get_doc(
			"Scheduled Job Type",
			dict(method="dontmanage.email.doctype.auto_email_report.auto_email_report.send_monthly"),
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertTrue(job.is_event_due(get_datetime("2019-02-01 00:00:01")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-15 00:00:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-31 23:59:59")))

	def test_cron_job(self):
		# runs every 10 mins
		job = dontmanage.get_doc(
			"Scheduled Job Type", dict(method="dontmanage.email.doctype.email_account.email_account.pull")
		)
		job.db_set("last_execution", "2019-01-01 00:00:00")
		self.assertEqual(job.next_execution, get_datetime("2019-01-01 00:10:00"))
		self.assertTrue(job.is_event_due(get_datetime("2019-01-01 00:10:01")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:05:06")))
		self.assertFalse(job.is_event_due(get_datetime("2019-01-01 00:09:59")))

	def test_maintenance_jobs(self):
		sjt = dontmanage.new_doc(
			"Scheduled Job Type",
			frequency="Hourly Maintenance",
			last_execution=get_datetime("2019-01-01 23:59:00"),
		)
		# Should be within one hour
		self.assertGreaterEqual(sjt.next_execution, sjt.last_execution)
		self.assertGreater(add_to_date(sjt.last_execution, hours=1), sjt.next_execution)

		# Next should be exactly one hour away
		sjt.last_execution = sjt.next_execution
		self.assertEqual(add_to_date(sjt.last_execution, hours=1), sjt.next_execution)

	def test_cold_start(self):
		now = now_datetime()
		just_before_12_am = now.replace(hour=11, minute=59, second=30)
		just_after_12_am = now.replace(hour=0, minute=0, second=30) + timedelta(days=1)

		job = dontmanage.new_doc("Scheduled Job Type")
		job.frequency = "Daily"
		job.set_user_and_timestamp()

		with self.freeze_time(just_before_12_am):
			self.assertFalse(job.is_event_due())

		with self.freeze_time(just_after_12_am):
			self.assertTrue(job.is_event_due())

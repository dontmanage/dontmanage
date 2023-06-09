# Copyright (c) 2015, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import time

import dontmanage
from dontmanage.auth import CookieManager, LoginManager
from dontmanage.tests.utils import DontManageTestCase


class TestActivityLog(DontManageTestCase):
	def test_activity_log(self):

		# test user login log
		dontmanage.local.form_dict = dontmanage._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": dontmanage.conf.admin_password or "admin",
				"usr": "Administrator",
			}
		)

		dontmanage.local.cookie_manager = CookieManager()
		dontmanage.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(dontmanage.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		dontmanage.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		dontmanage.form_dict.update({"pwd": "password"})
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		dontmanage.local.form_dict = dontmanage._dict()

	def get_auth_log(self, operation="Login"):
		names = dontmanage.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		auth_log = dontmanage.get_doc("Activity Log", name)
		return auth_log

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		dontmanage.local.form_dict = dontmanage._dict(
			{"cmd": "login", "sid": "Guest", "pwd": "admin", "usr": "Administrator"}
		)

		dontmanage.local.cookie_manager = CookieManager()
		dontmanage.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		dontmanage.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		dontmanage.form_dict.update({"pwd": "password"})
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)
		self.assertRaises(dontmanage.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(dontmanage.AuthenticationError, LoginManager)

		dontmanage.local.form_dict = dontmanage._dict()


def update_system_settings(args):
	doc = dontmanage.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()

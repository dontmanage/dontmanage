# Copyright (c) 2020, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests import IntegrationTestCase


class TestModuleProfile(IntegrationTestCase):
	def setUp(self):
		dontmanage.delete_doc_if_exists("Module Profile", "_Test Module Profile", force=1)
		dontmanage.delete_doc_if_exists("Module Profile", "_Test Module Profile 2", force=1)
		dontmanage.delete_doc_if_exists("User", "test-module-user1@example.com", force=1)
		dontmanage.delete_doc_if_exists("User", "test-module-user2@example.com", force=1)

	def test_make_new_module_profile(self):
		dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}],
			}
		).insert()

		new_user = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "Test User"}
		).insert()

		new_user.module_profile = "_Test Module Profile"
		new_user.save()

		self.assertEqual(new_user.block_modules[0].module, "Accounts")

	def test_multiple_block_modules(self):
		"""Assign multiple blocked modules from profile to user"""
		module_profile = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}, {"module": "CRM"}, {"module": "HR"}],
			}
		).insert()

		user = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "Test User"}
		).insert()

		user.module_profile = module_profile.name
		user.save()

		self.assertSetEqual({bm.module for bm in user.block_modules}, {"Accounts", "CRM", "HR"})

	def test_update_module_profile_propagates_to_users(self):
		"""Updating block_modules in profile should update linked users"""
		module_profile = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}],
			}
		).insert()

		user = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "Test User"}
		).insert()

		user.module_profile = module_profile.name
		user.save()

		self.assertEqual({bm.module for bm in user.block_modules}, {"Accounts"})

		module_profile.append("block_modules", {"module": "Projects"})
		module_profile.save()

		user.reload()
		self.assertSetEqual({bm.module for bm in user.block_modules}, {"Accounts", "Projects"})

	def test_clear_block_modules(self):
		"""Clearing block_modules in profile should also clear them for users"""
		module_profile = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}],
			}
		).insert()

		user = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "Test User"}
		).insert()

		user.module_profile = module_profile.name
		user.save()
		self.assertTrue(user.block_modules)

		module_profile.block_modules = []
		module_profile.save()

		user.reload()
		self.assertEqual(user.block_modules, [])

	def test_multiple_users_same_profile(self):
		"""Updates should propagate to all users linked to the same profile"""
		module_profile = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}],
			}
		).insert()

		user1 = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "User One"}
		).insert()
		user2 = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user2@example.com", "first_name": "User Two"}
		).insert()

		for u in (user1, user2):
			u.module_profile = module_profile.name
			u.save()

		module_profile.append("block_modules", {"module": "Projects"})
		module_profile.save()

		user1.reload()
		user2.reload()
		self.assertEqual([bm.module for bm in user1.block_modules], ["Accounts", "Projects"])
		self.assertEqual([bm.module for bm in user2.block_modules], ["Accounts", "Projects"])

	def test_switch_user_module_profile(self):
		"""Switching user to a different profile updates their block_modules"""
		profile1 = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile",
				"block_modules": [{"module": "Accounts"}],
			}
		).insert()
		profile2 = dontmanage.get_doc(
			{
				"doctype": "Module Profile",
				"module_profile_name": "_Test Module Profile 2",
				"block_modules": [{"module": "HR"}],
			}
		).insert()

		user = dontmanage.get_doc(
			{"doctype": "User", "email": "test-module-user1@example.com", "first_name": "Test User"}
		).insert()

		user.module_profile = profile1.name
		user.save()
		self.assertEqual([bm.module for bm in user.block_modules], ["Accounts"])

		user.module_profile = profile2.name
		user.save()
		self.assertEqual([bm.module for bm in user.block_modules], ["HR"])

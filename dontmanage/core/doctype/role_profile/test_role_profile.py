# Copyright (c) 2017, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests.utils import DontManageTestCase

test_dependencies = ["Role"]


class TestRoleProfile(DontManageTestCase):
	def test_make_new_role_profile(self):
		dontmanage.delete_doc_if_exists("Role Profile", "Test 1", force=1)
		new_role_profile = dontmanage.get_doc(dict(doctype="Role Profile", role_profile="Test 1")).insert()

		self.assertEqual(new_role_profile.role_profile, "Test 1")

		# add role
		new_role_profile.append("roles", {"role": "_Test Role 2"})
		new_role_profile.save()
		self.assertEqual(new_role_profile.roles[0].role, "_Test Role 2")

		# user with a role profile
		random_user = dontmanage.mock("email")
		random_user_name = dontmanage.mock("name")

		random_user = dontmanage.get_doc(
			{
				"doctype": "User",
				"email": random_user,
				"enabled": 1,
				"first_name": random_user_name,
				"new_password": "Eastern_43A1W",
				"role_profile_name": "Test 1",
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)
		self.assertListEqual(
			[role.role for role in random_user.roles], [role.role for role in new_role_profile.roles]
		)

		# clear roles
		new_role_profile.roles = []
		new_role_profile.save()
		self.assertEqual(new_role_profile.roles, [])

		# user roles with the role profile should also be updated
		random_user.reload()
		self.assertListEqual(random_user.roles, [])

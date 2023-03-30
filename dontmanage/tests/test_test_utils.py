import dontmanage
from dontmanage.tests.utils import DontManageTestCase, change_settings


class TestTestUtils(DontManageTestCase):
	SHOW_TRANSACTION_COMMIT_WARNINGS = True

	def test_document_assertions(self):

		currency = dontmanage.new_doc("Currency")
		currency.currency_name = "STONKS"
		currency.smallest_currency_fraction_value = 0.420_001
		currency.save()

		self.assertDocumentEqual(currency.as_dict(), currency)

	def test_thread_locals(self):
		dontmanage.flags.temp_flag_to_be_discarded = True

	def test_temp_setting_changes(self):
		current_setting = dontmanage.get_system_settings("logout_on_password_reset")

		with change_settings("System Settings", {"logout_on_password_reset": int(not current_setting)}):
			updated_settings = dontmanage.get_system_settings("logout_on_password_reset")
			self.assertNotEqual(current_setting, updated_settings)

		restored_settings = dontmanage.get_system_settings("logout_on_password_reset")
		self.assertEqual(current_setting, restored_settings)


def tearDownModule():
	"""assertions for ensuring tests didn't leave state behind"""
	assert "temp_flag_to_be_discarded" not in dontmanage.flags
	assert not dontmanage.db.exists("Currency", "STONKS")

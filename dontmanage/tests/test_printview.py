import dontmanage
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.www.printview import get_html_and_style


class PrintViewTest(DontManageTestCase):
	def test_print_view_without_errors(self):

		user = dontmanage.get_last_doc("User")

		messages_before = dontmanage.get_message_log()
		ret = get_html_and_style(doc=user.as_json(), print_format="Standard", no_letterhead=1)
		messages_after = dontmanage.get_message_log()

		if len(messages_after) > len(messages_before):
			new_messages = messages_after[len(messages_before) :]
			self.fail("Print view showing error/warnings: \n" + "\n".join(str(msg) for msg in new_messages))

		# html should exist
		self.assertTrue(bool(ret["html"]))

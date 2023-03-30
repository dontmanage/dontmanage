import dontmanage
from dontmanage import format
from dontmanage.tests.utils import DontManageTestCase


class TestFormatter(DontManageTestCase):
	def test_currency_formatting(self):
		df = dontmanage._dict({"fieldname": "amount", "fieldtype": "Currency", "options": "currency"})

		doc = dontmanage._dict({"amount": 5})
		dontmanage.db.set_default("currency", "INR")

		# if currency field is not passed then default currency should be used.
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "₹ 100,000.00")

		doc.currency = "USD"
		self.assertEqual(format(100000, df, doc, format="#,###.##"), "$ 100,000.00")

		dontmanage.db.set_default("currency", None)

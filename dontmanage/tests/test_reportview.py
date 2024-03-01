# Copyright (c) 2019, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.desk.reportview import export_query
from dontmanage.tests.utils import DontManageTestCase


class TestReportview(DontManageTestCase):
	def test_csv(self):
		from csv import QUOTE_ALL, QUOTE_MINIMAL, QUOTE_NONE, QUOTE_NONNUMERIC, DictReader
		from io import StringIO

		dontmanage.local.form_dict = dontmanage._dict(
			doctype="DocType",
			file_format_type="CSV",
			fields=("name", "module", "issingle"),
			filters={"issingle": 1, "module": "Core"},
		)

		for delimiter in (",", ";", "\t", "|"):
			dontmanage.local.form_dict.csv_delimiter = delimiter
			for quoting in (QUOTE_ALL, QUOTE_MINIMAL, QUOTE_NONE, QUOTE_NONNUMERIC):
				dontmanage.local.form_dict.csv_quoting = quoting

				export_query()

				self.assertTrue(dontmanage.response["filename"].endswith(".csv"))
				self.assertEqual(dontmanage.response["type"], "binary")
				with StringIO(dontmanage.response["filecontent"].decode("utf-8")) as result:
					reader = DictReader(result, delimiter=delimiter, quoting=quoting)
					for row in reader:
						self.assertEqual(int(row["Is Single"]), 1)
						self.assertEqual(row["Module"], "Core")

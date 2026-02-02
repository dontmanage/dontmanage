# Copyright (c) 2024, DontManage Technologies and Contributors
# See license.txt

import dontmanage
from dontmanage.desk.form.load import getdoc
from dontmanage.tests import IntegrationTestCase


class TestSystemHealthReport(IntegrationTestCase):
	def test_it_works(self):
		getdoc("System Health Report", "System Health Report")

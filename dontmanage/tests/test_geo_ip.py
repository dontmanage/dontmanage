# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
from dontmanage.tests.utils import DontManageTestCase


class TestGeoIP(DontManageTestCase):
	def test_geo_ip(self):
		return
		from dontmanage.sessions import get_geo_ip_country

		self.assertEqual(get_geo_ip_country("223.29.223.255"), "India")
		self.assertEqual(get_geo_ip_country("4.18.32.80"), "United States")
		self.assertEqual(get_geo_ip_country("217.194.147.25"), "United States")

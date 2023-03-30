import dontmanage
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import get_html_for_route


class TestSitemap(DontManageTestCase):
	def test_sitemap(self):
		from dontmanage.test_runner import make_test_records

		make_test_records("Blog Post")
		blogs = dontmanage.get_all("Blog Post", {"published": 1}, ["route"], limit=1)
		xml = get_html_for_route("sitemap.xml")
		self.assertTrue("/about</loc>" in xml)
		self.assertTrue("/contact</loc>" in xml)
		self.assertTrue(blogs[0].route in xml)

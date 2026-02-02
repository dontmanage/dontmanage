# Copyright (c) 2017, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests import IntegrationTestCase


class TestLetterHead(IntegrationTestCase):
	def test_auto_image(self):
		letter_head = dontmanage.get_doc(
			doctype="Letter Head", letter_head_name="Test", source="Image", image="/public/test.png"
		).insert()

		# test if image is automatically set
		self.assertTrue(letter_head.image in letter_head.content)

# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import os

import dontmanage
from dontmanage.model.document import Document


class Package(Document):
	def validate(self):
		if not self.package_name:
			self.package_name = self.name.lower().replace(" ", "-")


@dontmanage.whitelist()
def get_license_text(license_type):
	with open(os.path.join(os.path.dirname(__file__), "licenses", license_type + ".md")) as textfile:
		return textfile.read()

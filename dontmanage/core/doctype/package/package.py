# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import os

import dontmanage
from dontmanage.model.document import Document

LICENSES = (
	"GNU Affero General Public License",
	"GNU General Public License",
	"MIT License",
)


class Package(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		license: DF.MarkdownEditor | None
		license_type: DF.Literal[
			"", "MIT License", "GNU General Public License", "GNU Affero General Public License"
		]
		package_name: DF.Data
		readme: DF.MarkdownEditor | None

	# end: auto-generated types
	def validate(self):
		if not self.package_name:
			self.package_name = self.name.lower().replace(" ", "-")


@dontmanage.whitelist()
def get_license_text(license_type: str) -> str | None:
	if license_type in LICENSES:
		with open(os.path.join(os.path.dirname(__file__), "licenses", license_type + ".md")) as textfile:
			return textfile.read()

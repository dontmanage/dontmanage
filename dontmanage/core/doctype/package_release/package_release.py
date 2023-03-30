# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import os
import subprocess

import dontmanage
from dontmanage.model.document import Document
from dontmanage.modules.export_file import export_doc
from dontmanage.query_builder.functions import Max


class PackageRelease(Document):
	def set_version(self):
		# set the next patch release by default
		doctype = dontmanage.qb.DocType("Package Release")
		if not self.major:
			self.major = (
				dontmanage.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max(doctype.minor))
				.run()[0][0]
				or 0
			)

		if not self.minor:
			self.minor = (
				dontmanage.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max("minor"))
				.run()[0][0]
				or 0
			)
		if not self.patch:
			value = (
				dontmanage.qb.from_(doctype)
				.where(doctype.package == self.package)
				.select(Max("patch"))
				.run()[0][0]
				or 0
			)
			self.patch = value + 1

	def autoname(self):
		self.set_version()
		self.name = "{}-{}.{}.{}".format(
			dontmanage.db.get_value("Package", self.package, "package_name"), self.major, self.minor, self.patch
		)

	def validate(self):
		if self.publish:
			self.export_files()

	def export_files(self):
		"""Export all the documents in this package to site/packages folder"""
		package = dontmanage.get_doc("Package", self.package)

		self.export_modules()
		self.export_package_files(package)
		self.make_tarfile(package)

	def export_modules(self):
		for m in dontmanage.get_all("Module Def", dict(package=self.package)):
			module = dontmanage.get_doc("Module Def", m.name)
			for l in module.meta.links:
				if l.link_doctype == "Module Def":
					continue
				# all documents of the type in the module
				for d in dontmanage.get_all(l.link_doctype, dict(module=m.name)):
					export_doc(dontmanage.get_doc(l.link_doctype, d.name))

	def export_package_files(self, package):
		# write readme
		with open(dontmanage.get_site_path("packages", package.package_name, "README.md"), "w") as readme:
			readme.write(package.readme)

		# write license
		if package.license:
			with open(dontmanage.get_site_path("packages", package.package_name, "LICENSE.md"), "w") as license:
				license.write(package.license)

		# write package.json as `dontmanage_package.json`
		with open(
			dontmanage.get_site_path("packages", package.package_name, package.package_name + ".json"), "w"
		) as packagefile:
			packagefile.write(dontmanage.as_json(package.as_dict(no_nulls=True)))

	def make_tarfile(self, package):
		# make tarfile
		filename = f"{self.name}.tar.gz"
		subprocess.check_output(
			["tar", "czf", filename, package.package_name], cwd=dontmanage.get_site_path("packages")
		)

		# move file
		subprocess.check_output(
			["mv", dontmanage.get_site_path("packages", filename), dontmanage.get_site_path("public", "files")]
		)

		# make attachment
		file = dontmanage.get_doc(
			dict(
				doctype="File",
				file_url="/" + os.path.join("files", filename),
				attached_to_doctype=self.doctype,
				attached_to_name=self.name,
			)
		)

		file.flags.ignore_duplicate_entry_error = True
		file.insert()

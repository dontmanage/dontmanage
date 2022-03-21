# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import io
import mimetypes
import os
import re
import shutil
from typing import Union, List
import zipfile

from requests.exceptions import HTTPError, SSLError
from PIL import Image, ImageFile, ImageOps
from urllib.parse import quote, unquote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import call_hook_method, cint, encode, get_files_path, get_hook_method
from frappe.utils.image import strip_exif_data, optimize_image
from frappe.utils.file_manager import is_safe_path, safe_b64decode

from .exceptions import MaxFileSizeReachedError, FolderNotEmpty
from .utils import *


exclude_from_linked_with = True
ImageFile.LOAD_TRUNCATED_IMAGES = True


class File(Document):
	no_feed_on_delete = True

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.content = self.get("content", None)
		self.decode = self.get("decode", False)

	def autoname(self):
		"""Set name for folder"""
		if self.is_folder:
			if self.folder:
				self.name = self.get_name_based_on_parent_folder()
			else:
				# home
				self.name = self.file_name
		else:
			self.name = frappe.generate_hash(length=10)

	def before_insert(self):
		self.set_folder_name()
		self.set_file_name()

		if not self.is_folder:
			self.flags.new_file = True
			frappe.local.rollback_observers.append(self)
			self.save_file(content=self.content, decode=self.decode)

	def after_insert(self):
		if not self.is_folder:
			self.create_attachment_record()
		self.set_is_private()
		self.set_file_name()
		self.validate_duplicate_entry()
		self.validate_attachment_limit()

	def validate(self):
		# Ensure correct formatting and type
		self.file_url = unquote(self.file_url) if self.file_url else ""

		if not self.is_new() and self.has_value_changed("is_private"):
			self.handle_is_private_changed()

		if not self.is_folder:
			self.validate_file_path()
			self.validate_file_url()
			self.validate_file_on_disk()

		self.file_size = frappe.form_dict.file_size or self.file_size

	def after_rename(self, *args, **kwargs):
		for successor in self.get_successors():
			setup_folder_path(successor, self.name)

	def on_trash(self):
		if self.is_home_folder or self.is_attachments_folder:
			frappe.throw(_("Cannot delete Home and Attachments folders"))
		self.validate_empty_folder()
		self._delete_file_on_disk()
		if not self.is_folder:
			self.add_comment_in_reference_doc(
				"Attachment Removed", _("Removed {0}").format(self.file_name)
			)

	def on_rollback(self):
		# if original_content flag is set, this rollback should revert the file to its original state
		if self.flags.original_content:
			file_path = self.get_full_path()
			with open(file_path, "wb+") as f:
				f.write(self.flags.original_content)
				os.fsync(f.fileno())

		# used in case file path (File.file_url) has been changed
		if self.flags.original_path:
			target = self.flags.original_path["old"]
			source = self.flags.original_path["new"]
			shutil.move(source, target)

		# following condition is only executed when an insert has been rolledback
		if self.flags.new_file:
			self._delete_file_on_disk()

	def get_name_based_on_parent_folder(self) -> Union[str, None]:
		if self.folder:
			return os.path.join(self.folder, self.file_name)

	def get_successors(self):
		return frappe.get_all(
			"File", filters={"folder": self.name}, pluck="name"
		)

	def validate_file_path(self):
		if self.file_url.startswith(("http://", "https://")):
			return

		base_path = os.path.realpath(get_files_path(is_private=self.is_private))
		if not os.path.realpath(self.get_full_path()).startswith(base_path):
			frappe.throw(
				_("The File URL you've entered is incorrect"),
				title=_("Invalid File URL"),
			)

	def validate_file_url(self):
		if self.file_url.startswith(("http://", "https://")):
			return

		if not self.file_url:
			return

		if not self.file_url.startswith(("/files/", "/private/files/")):
			# Probably an invalid URL since it doesn't start with http either
			frappe.throw(
				_("URL must start with http:// or https://"),
				title=_("Invalid URL"),
			)

	def handle_is_private_changed(self):
		from pathlib import Path

		old_file_url = self.file_url
		file_name = self.file_url.split("/")[-1]
		private_file_path = Path(frappe.get_site_path("private", "files", file_name))
		public_file_path = Path(frappe.get_site_path("public", "files", file_name))

		if cint(self.is_private):
			source = public_file_path
			target = private_file_path
			url_starts_with = "/private/files/"
		else:
			source = private_file_path
			target = public_file_path
			url_starts_with = "/files/"

		if not source.exists():
			frappe.throw(
				_("Cannot find file {} on disk").format(source),
				exc=FileNotFoundError,
			)
		if target.exists():
			frappe.throw(
				_("A file with same name {} already exists").format(target),
				exc=FileExistsError,
			)

		# Uses os.rename which is an atomic operation
		shutil.move(source, target)
		self.flags.original_path = {"old": source, "new": target}
		frappe.local.rollback_observers.append(self)

		self.file_url = f"{url_starts_with}{file_name}"
		update_existing_file_docs(self)

		if (
			not self.attached_to_doctype
			or not self.attached_to_name
			or not self.fetch_attached_to_field(old_file_url)
		):
			return

		frappe.db.set_value(
			self.attached_to_doctype,
			self.attached_to_name,
			self.attached_to_field,
			self.file_url,
		)

	def fetch_attached_to_field(self, old_file_url):
		if self.attached_to_field:
			return True

		reference_dict = frappe.get_doc(
			self.attached_to_doctype, self.attached_to_name).as_dict()

		for key, value in reference_dict.items():
			if value == old_file_url:
				self.attached_to_field = key
				return True

	def validate_attachment_limit(self):
		attachment_limit = 0
		if self.attached_to_doctype and self.attached_to_name:
			attachment_limit = cint(frappe.get_meta(self.attached_to_doctype).max_attachments)

		if attachment_limit:
			current_attachment_count = len(frappe.get_all('File', filters={
				'attached_to_doctype': self.attached_to_doctype,
				'attached_to_name': self.attached_to_name,
			}, limit=attachment_limit + 1))

			if current_attachment_count >= attachment_limit:
				frappe.throw(
					_("Maximum Attachment Limit of {0} has been reached for {1} {2}.").format(
						frappe.bold(attachment_limit), self.attached_to_doctype, self.attached_to_name
					),
					exc=frappe.exceptions.AttachmentLimitReached,
					title=_('Attachment Limit Reached')
				)

	def set_folder_name(self):
		"""Make parent folders if not exists based on reference doctype and name"""
		if self.folder:
			return

		if self.attached_to_doctype:
			self.folder = frappe.db.get_value("File", {"is_attachments_folder": 1})

		if not self.is_home_folder:
			self.folder = "Home"

	def validate_file_on_disk(self):
		"""Validates existence file
		"""
		full_path = self.get_full_path()

		if full_path.startswith("http"):
			return True

		if not os.path.exists(full_path):
			frappe.throw(_("File {0} does not exist").format(self.file_url), IOError)

	def validate_duplicate_entry(self):
		if not self.flags.ignore_duplicate_entry_error and not self.is_folder:
			if not self.content_hash:
				self.generate_content_hash()

			# check duplicate name
			# check duplicate assignment
			filters = {
				"content_hash": self.content_hash,
				"is_private": self.is_private,
				"name": ("!=", self.name),
			}
			if self.attached_to_doctype and self.attached_to_name:
				filters.update(
					{
						"attached_to_doctype": self.attached_to_doctype,
						"attached_to_name": self.attached_to_name,
					}
				)
			duplicate_file = frappe.db.get_value(
				"File", filters, ["name", "file_url"], as_dict=1
			)

			if duplicate_file:
				duplicate_file_doc = frappe.get_cached_doc("File", duplicate_file.name)
				if duplicate_file_doc.exists_on_disk():
					# just use the url, to avoid uploading a duplicate
					self.file_url = duplicate_file.file_url

	def set_file_name(self):
		if not self.file_name and self.file_url:
			self.file_name = self.file_url.split("/")[-1]
		else:
			self.file_name = re.sub(r"/", "", self.file_name)

	def generate_content_hash(self):
		if self.content_hash or not self.file_url or self.file_url.startswith("http"):
			return
		file_name = self.file_url.split("/")[-1]
		try:
			file_path = get_files_path(file_name, is_private=self.is_private)
			with open(file_path, "rb") as f:
				self.content_hash = get_content_hash(f.read())
		except IOError:
			frappe.throw(_("File {0} does not exist").format(file_path))

	def make_thumbnail(
		self,
		set_as_thumbnail: bool = True,
		width: int = 300,
		height: int = 300,
		suffix: str = "small",
		crop: bool = False,
	) -> str:
		if not self.file_url:
			return

		try:
			if self.file_url.startswith(("/files", "/private/files")):
				image, filename, extn = get_local_image(self.file_url)
			else:
				image, filename, extn = get_web_image(self.file_url)
		except (HTTPError, SSLError, IOError, TypeError):
			return

		size = width, height
		if crop:
			image = ImageOps.fit(image, size, Image.ANTIALIAS)
		else:
			image.thumbnail(size, Image.ANTIALIAS)

		thumbnail_url = f"{filename}_{suffix}.{extn}"
		path = os.path.abspath(
			frappe.get_site_path("public", thumbnail_url.lstrip("/"))
		)

		try:
			image.save(path)
			if set_as_thumbnail:
				self.db_set("thumbnail_url", thumbnail_url)

		except IOError:
			frappe.msgprint(_("Unable to write file format for {0}").format(path))
			return

		return thumbnail_url

	def validate_empty_folder(self):
		"""Throw exception if folder is not empty"""
		if self.is_folder and frappe.get_all("File", filters={"folder": self.name}, limit=1):
			frappe.throw(_("Folder {0} is not empty").format(self.name), FolderNotEmpty)

	def _delete_file_on_disk(self):
		"""If file not attached to any other record, delete it"""
		on_disk_file_not_shared = (
			self.content_hash
			and not frappe.get_all("File",
				filters={"content_hash": self.content_hash, "name": ["!=", self.name]},
				limit=1,
			)
		)
		if self.file_name and on_disk_file_not_shared:
			self.delete_file_data_content()
		elif self.file_url:
			self.delete_file_data_content(only_thumbnail=True)

	def unzip(self) -> List["File"]:
		"""Unzip current file and replace it by its children"""
		if not self.file_url.endswith(".zip"):
			frappe.throw(_("{0} is not a zip file").format(self.file_name))

		zip_path = self.get_full_path()

		files = []
		with zipfile.ZipFile(zip_path) as z:
			for file in z.filelist:
				if file.is_dir() or file.filename.startswith("__MACOSX/"):
					# skip directories and macos hidden directory
					continue

				filename = os.path.basename(file.filename)
				if filename.startswith("."):
					# skip hidden files
					continue

				file_doc = frappe.new_doc("File")
				file_doc.content = z.read(file.filename)
				file_doc.file_name = filename
				file_doc.folder = self.folder
				file_doc.is_private = self.is_private
				file_doc.attached_to_doctype = self.attached_to_doctype
				file_doc.attached_to_name = self.attached_to_name
				file_doc.save()
				files.append(file_doc)

		frappe.delete_doc("File", self.name)
		return files

	def exists_on_disk(self):
		return os.path.exists(self.get_full_path())

	def get_content(self) -> bytes:
		"""Returns [`file_name`, `content`] for given file name `fname`"""
		if self.is_folder:
			frappe.throw(_("Cannot get file contents of a Folder"))

		if self.get("content"):
			return self.content

		self.validate_file_url()
		file_path = self.get_full_path()

		# read the file
		with io.open(encode(file_path), mode="rb") as f:
			self.content = f.read()
			try:
				# for plain text files
				self.content = self.content.decode()
			except UnicodeDecodeError:
				# for .png, .jpg, etc
				pass

		return self.content

	def get_full_path(self):
		"""Returns file path from given file name"""

		file_path = self.file_url or self.file_name

		if "/" not in file_path:
			file_path = "/files/" + file_path

		if file_path.startswith("/private/files/"):
			file_path = get_files_path(
				*file_path.split("/private/files/", 1)[1].split("/"), is_private=1
			)

		elif file_path.startswith("/files/"):
			file_path = get_files_path(*file_path.split("/files/", 1)[1].split("/"))

		elif file_path.startswith("http"):
			pass

		elif not self.file_url:
			frappe.throw(
				_("There is some problem with the file url: {0}").format(file_path)
			)

		if not is_safe_path(file_path):
			frappe.throw(f"Cannot access file path {file_path}")

		return file_path

	def write_file(self):
		"""write file to disk with a random name (to compare)"""
		file_path = get_files_path(is_private=self.is_private)

		if os.path.sep in self.file_name:
			frappe.throw(_("File name cannot have {0}").format(os.path.sep))

		# create directory (if not exists)
		frappe.create_folder(file_path)
		# write the file
		self.content = self.get_content()
		if isinstance(self.content, str):
			self.content = self.content.encode()
		_file_path = os.path.join(file_path.encode("utf-8"), self.file_name.encode("utf-8"))
		with open(_file_path, "wb+") as f:
			f.write(self.content)
			os.fsync(f.fileno())
		frappe.local.rollback_observers.append(self)

		return get_files_path(self.file_name, is_private=self.is_private)

	def save_file(self, content=None, decode=False, ignore_existing_file_check=False, overwrite=False):
		self.flags.original_content = self.get_content()
		if not self.content:
			return

		file_exists = False
		duplicate_file = None

		self.content = content
		self.is_private = cint(self.is_private)
		self.content_type = mimetypes.guess_type(self.file_name)[0]
		self.file_size = self.check_max_file_size()

		# decode self.content
		if decode:
			if isinstance(content, str):
				self.content = content.encode("utf-8")

			if b"," in self.content:
				self.content = self.content.split(b",")[1]
			self.content = safe_b64decode(self.content)

		# transform file content based on site settings
		if (
			self.content_type
			and self.content_type == "image/jpeg"
			and frappe.get_system_settings("strip_exif_metadata_from_uploaded_images")
		):
			self.content = strip_exif_data(self.content, self.content_type)

		self.content_hash = get_content_hash(self.content)

		# check if a file exists with the same content hash and is also in the same folder (public or private)
		if not ignore_existing_file_check:
			duplicate_file = frappe.get_value(
				"File",
				{"content_hash": self.content_hash, "is_private": self.is_private},
				["file_url", "name"],
				as_dict=True,
			)

		if duplicate_file:
			file_doc = frappe.get_cached_doc("File", duplicate_file.name)
			if file_doc.exists_on_disk():
				self.file_url = duplicate_file.file_url
				file_exists = True

		if not file_exists:
			if not overwrite:
				self.file_name = generate_file_name(
					name=self.file_name,
					suffix=self.content_hash[-6:],
					is_private=self.is_private,
				)
			call_hook_method("before_write_file", file_size=self.file_size)
			write_file_method = get_hook_method("write_file")
			if write_file_method:
				return write_file_method(self)
			return self.save_file_on_filesystem()

	def save_file_on_filesystem(self):
		fpath = self.write_file()

		if self.is_private:
			self.file_url = f"/private/files/{self.file_name}"
		else:
			self.file_url = f"/files/{self.file_name}"

		return {"file_name": os.path.basename(fpath), "file_url": self.file_url}

	def check_max_file_size(self):
		from frappe.core.api.file import get_max_file_size

		max_file_size = get_max_file_size()
		file_size = len(self.content)

		if file_size > max_file_size:
			frappe.throw(
				_("File size exceeded the maximum allowed size of {0} MB").format(
					max_file_size / 1048576
				),
				exc=MaxFileSizeReachedError,
			)

		return file_size

	def delete_file_data_content(self, only_thumbnail=False):
		method = get_hook_method("delete_file_data_content")
		if method:
			method(self, only_thumbnail=only_thumbnail)
		else:
			self.delete_file_from_filesystem(only_thumbnail=only_thumbnail)

	def delete_file_from_filesystem(self, only_thumbnail=False):
		"""Delete file, thumbnail from File document"""
		if only_thumbnail:
			delete_file(self.thumbnail_url)
		else:
			delete_file(self.file_url)
			delete_file(self.thumbnail_url)

	def is_downloadable(self):
		return has_permission(self, "read")

	def get_extension(self):
		"""returns split filename and extension"""
		return os.path.splitext(self.file_name)

	def create_attachment_record(self):
		icon = ' <i class="fa fa-lock text-warning"></i>' if self.is_private else ""
		file_url = quote(frappe.safe_encode(self.file_url)) if self.file_url else self.file_name
		file_name = self.file_name or self.file_url

		self.add_comment_in_reference_doc(
			"Attachment",
			_("Added {0}").format(f"<a href='{file_url}' target='_blank'>{file_name}</a>{icon}"),
		)

	def add_comment_in_reference_doc(self, comment_type, text):
		if self.attached_to_doctype and self.attached_to_name:
			try:
				doc = frappe.get_doc(self.attached_to_doctype, self.attached_to_name)
				doc.add_comment(comment_type, text)
			except frappe.DoesNotExistError:
				frappe.clear_messages()

	def set_is_private(self):
		if self.file_url:
			self.is_private = cint(self.file_url.startswith("/private"))

	@frappe.whitelist()
	def optimize_file(self):
		if self.is_folder:
			raise TypeError("Folders cannot be optimized")

		content_type = mimetypes.guess_type(self.file_name)[0]
		is_local_image = content_type.startswith("image/") and self.file_size > 0
		is_svg = content_type == "image/svg+xml"

		if not is_local_image:
			raise NotImplementedError("Only local image files can be optimized")

		if is_svg:
			raise TypeError("Optimization of SVG images is not supported")

		optimized_content = optimize_image(
			content=self.get_content(),
			content_type=content_type,
		)

		self.save_file(content=optimized_content, overwrite=True)
		self.save()

	@staticmethod
	def zip_files(files):
		zip_file = io.BytesIO()
		zf = zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED)
		for _file in files:
			if isinstance(_file, str):
				_file = frappe.get_doc("File", _file)
			if not isinstance(_file, File):
				continue
			if _file.is_folder:
				continue
			zf.writestr(_file.file_name, _file.get_content())
		zf.close()
		return zip_file.getvalue()


def on_doctype_update():
	frappe.db.add_index("File", ["attached_to_doctype", "attached_to_name"])


def has_permission(doc, ptype=None, user=None):
	has_access = False
	user = user or frappe.session.user

	if ptype == 'create':
		has_access = frappe.has_permission('File', 'create', user=user)

	if not doc.is_private or doc.owner in [user, 'Guest'] or user == 'Administrator':
		has_access = True

	if doc.attached_to_doctype and doc.attached_to_name:
		attached_to_doctype = doc.attached_to_doctype
		attached_to_name = doc.attached_to_name

		try:
			ref_doc = frappe.get_doc(attached_to_doctype, attached_to_name)

			if ptype in ['write', 'create', 'delete']:
				has_access = ref_doc.has_permission('write')

				if ptype == 'delete' and not has_access:
					frappe.throw(_("Cannot delete file as it belongs to {0} {1} for which you do not have permissions").format(
						doc.attached_to_doctype, doc.attached_to_name),
						frappe.PermissionError)
			else:
				has_access = ref_doc.has_permission('read')
		except frappe.DoesNotExistError:
			# if parent doc is not created before file is created
			# we cannot check its permission so we will use file's permission
			pass

	return has_access


# Note: kept at the end to not cause circular, partial imports & maintain backwards compatibility
from frappe.core.api.file import *

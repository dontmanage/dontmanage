# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class PatchLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		patch: DF.Code | None
		skipped: DF.Check
		traceback: DF.Code | None
	# end: auto-generated types
	pass


def before_migrate():
	dontmanage.reload_doc("core", "doctype", "patch_log")

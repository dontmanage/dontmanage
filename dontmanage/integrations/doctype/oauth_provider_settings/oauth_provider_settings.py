# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class OAuthProviderSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		skip_authorization: DF.Literal["Force", "Auto"]
	# end: auto-generated types

	pass

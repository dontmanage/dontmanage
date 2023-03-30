# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class OAuthProviderSettings(Document):
	pass


def get_oauth_settings():
	"""Returns oauth settings"""
	out = dontmanage._dict(
		{
			"skip_authorization": dontmanage.db.get_single_value(
				"OAuth Provider Settings", "skip_authorization"
			)
		}
	)

	return out

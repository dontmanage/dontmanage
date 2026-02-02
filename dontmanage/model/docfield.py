# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

"""docfield utililtes"""

import dontmanage


def supports_translation(fieldtype):
	return fieldtype in ["Data", "Select", "Text", "Small Text", "Text Editor"]

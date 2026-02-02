# Copyright (c) 2018, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")

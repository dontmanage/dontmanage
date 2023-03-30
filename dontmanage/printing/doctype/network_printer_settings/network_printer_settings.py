# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class NetworkPrinterSettings(Document):
	@dontmanage.whitelist()
	def get_printers_list(self, ip="localhost", port=631):
		printer_list = []
		try:
			import cups
		except ImportError:
			dontmanage.throw(
				_(
					"""This feature can not be used as dependencies are missing.
				Please contact your system manager to enable this by installing pycups!"""
				)
			)
			return
		try:
			cups.setServer(self.server_ip)
			cups.setPort(self.port)
			conn = cups.Connection()
			printers = conn.getPrinters()
			for printer_id, printer in printers.items():
				printer_list.append({"value": printer_id, "label": printer["printer-make-and-model"]})

		except RuntimeError:
			dontmanage.throw(_("Failed to connect to server"))
		except dontmanage.ValidationError:
			dontmanage.throw(_("Failed to connect to server"))
		return printer_list


@dontmanage.whitelist()
def get_network_printer_settings():
	return dontmanage.db.get_list("Network Printer Settings", pluck="name")

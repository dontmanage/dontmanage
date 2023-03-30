import os

from PyPDF2 import PdfWriter

import dontmanage
from dontmanage import _
from dontmanage.core.doctype.access_log.access_log import make_access_log
from dontmanage.translate import print_language
from dontmanage.utils.pdf import get_pdf

no_cache = 1

base_template_path = "www/printview.html"
standard_format = "templates/print_formats/standard.html"

from dontmanage.www.printview import validate_print_permission


@dontmanage.whitelist()
def download_multi_pdf(doctype, name, format=None, no_letterhead=False, options=None):
	"""
	Concatenate multiple docs as PDF .

	Returns a PDF compiled by concatenating multiple documents. The documents
	can be from a single DocType or multiple DocTypes

	Note: The design may seem a little weird, but it exists exists to
	        ensure backward compatibility. The correct way to use this function is to
	        pass a dict to doctype as described below

	NEW FUNCTIONALITY
	=================
	Parameters:
	doctype (dict):
	        key (string): DocType name
	        value (list): of strings of doc names which need to be concatenated and printed
	name (string):
	        name of the pdf which is generated
	format:
	        Print Format to be used

	Returns:
	PDF: A PDF generated by the concatenation of the mentioned input docs

	OLD FUNCTIONALITY - soon to be deprecated
	=========================================
	Parameters:
	doctype (string):
	        name of the DocType to which the docs belong which need to be printed
	name (string or list):
	        If string the name of the doc which needs to be printed
	        If list the list of strings of doc names which needs to be printed
	format:
	        Print Format to be used

	Returns:
	PDF: A PDF generated by the concatenation of the mentioned input docs
	"""

	import json

	output = PdfWriter()

	if isinstance(options, str):
		options = json.loads(options)

	if not isinstance(doctype, dict):
		result = json.loads(name)

		# Concatenating pdf files
		for i, ss in enumerate(result):
			output = dontmanage.get_print(
				doctype,
				ss,
				format,
				as_pdf=True,
				output=output,
				no_letterhead=no_letterhead,
				pdf_options=options,
			)
		dontmanage.local.response.filename = "{doctype}.pdf".format(
			doctype=doctype.replace(" ", "-").replace("/", "-")
		)
	else:
		for doctype_name in doctype:
			for doc_name in doctype[doctype_name]:
				try:
					output = dontmanage.get_print(
						doctype_name,
						doc_name,
						format,
						as_pdf=True,
						output=output,
						no_letterhead=no_letterhead,
						pdf_options=options,
					)
				except Exception:
					dontmanage.log_error(
						title="Error in Multi PDF download",
						message=f"Permission Error on doc {doc_name} of doctype {doctype_name}",
						reference_doctype=doctype_name,
						reference_name=doc_name,
					)
		dontmanage.local.response.filename = f"{name}.pdf"

	dontmanage.local.response.filecontent = read_multi_pdf(output)
	dontmanage.local.response.type = "download"


def read_multi_pdf(output):
	# Get the content of the merged pdf files
	fname = os.path.join("/tmp", f"dontmanage-pdf-{dontmanage.generate_hash()}.pdf")
	output.write(open(fname, "wb"))

	with open(fname, "rb") as fileobj:
		filedata = fileobj.read()

	return filedata


@dontmanage.whitelist(allow_guest=True)
def download_pdf(
	doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None
):
	doc = doc or dontmanage.get_doc(doctype, name)
	validate_print_permission(doc)

	with print_language(language):
		pdf_file = dontmanage.get_print(
			doctype, name, format, doc=doc, as_pdf=True, letterhead=letterhead, no_letterhead=no_letterhead
		)

	dontmanage.local.response.filename = "{name}.pdf".format(
		name=name.replace(" ", "-").replace("/", "-")
	)
	dontmanage.local.response.filecontent = pdf_file
	dontmanage.local.response.type = "pdf"


@dontmanage.whitelist()
def report_to_pdf(html, orientation="Landscape"):
	make_access_log(file_type="PDF", method="PDF", page=html)
	dontmanage.local.response.filename = "report.pdf"
	dontmanage.local.response.filecontent = get_pdf(html, {"orientation": orientation})
	dontmanage.local.response.type = "pdf"


@dontmanage.whitelist()
def print_by_server(
	doctype, name, printer_setting, print_format=None, doc=None, no_letterhead=0, file_path=None
):
	print_settings = dontmanage.get_doc("Network Printer Settings", printer_setting)
	try:
		import cups
	except ImportError:
		dontmanage.throw(_("You need to install pycups to use this feature!"))

	try:
		cups.setServer(print_settings.server_ip)
		cups.setPort(print_settings.port)
		conn = cups.Connection()
		output = PdfWriter()
		output = dontmanage.get_print(
			doctype, name, print_format, doc=doc, no_letterhead=no_letterhead, as_pdf=True, output=output
		)
		if not file_path:
			file_path = os.path.join("/", "tmp", f"dontmanage-pdf-{dontmanage.generate_hash()}.pdf")
		output.write(open(file_path, "wb"))
		conn.printFile(print_settings.printer_name, file_path, name, {})
	except OSError as e:
		if (
			"ContentNotFoundError" in e.message
			or "ContentOperationNotPermittedError" in e.message
			or "UnknownContentError" in e.message
			or "RemoteHostClosedError" in e.message
		):
			dontmanage.throw(_("PDF generation failed"))
	except cups.IPPError:
		dontmanage.throw(_("Printing failed"))

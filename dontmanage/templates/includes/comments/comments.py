# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import re

import dontmanage
from dontmanage import _, scrub
from dontmanage.rate_limiter import rate_limit
from dontmanage.utils.html_utils import clean_html
from dontmanage.website.doctype.blog_settings.blog_settings import get_comment_limit
from dontmanage.website.utils import clear_cache

URLS_COMMENT_PATTERN = re.compile(
	r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", re.IGNORECASE
)
EMAIL_PATTERN = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", re.IGNORECASE)


@dontmanage.whitelist(allow_guest=True)
@rate_limit(key="reference_name", limit=get_comment_limit, seconds=60 * 60)
def add_comment(comment, comment_email, comment_by, reference_doctype, reference_name, route):
	doc = dontmanage.get_doc(reference_doctype, reference_name)

	if dontmanage.session.user == "Guest" and doc.doctype not in ["Blog Post", "Web Page"]:
		return

	if not comment.strip():
		dontmanage.msgprint(_("The comment cannot be empty"))
		return False

	if URLS_COMMENT_PATTERN.search(comment) or EMAIL_PATTERN.search(comment):
		dontmanage.msgprint(_("Comments cannot have links or email addresses"))
		return False

	comment = doc.add_comment(
		text=clean_html(comment), comment_email=comment_email, comment_by=comment_by
	)

	comment.db_set("published", 1)

	# since comments are embedded in the page, clear the web cache
	if route:
		clear_cache(route)

	if doc.get("route"):
		url = f"{dontmanage.utils.get_request_site_address()}/{doc.route}#{comment.name}"
	else:
		url = f"{dontmanage.utils.get_request_site_address()}/app/{scrub(doc.doctype)}/{doc.name}#comment-{comment.name}"

	content = comment.content + "<p><a href='{}' style='font-size: 80%'>{}</a></p>".format(
		url, _("View Comment")
	)

	if doc.doctype == "Blog Post" and not doc.enable_email_notification:
		pass
	else:
		# notify creator
		creator_email = dontmanage.db.get_value("User", doc.owner, "email") or doc.owner
		subject = _("New Comment on {0}: {1}").format(doc.doctype, doc.get_title())

		dontmanage.sendmail(
			recipients=creator_email,
			subject=subject,
			message=content,
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)

	# revert with template if all clear (no backlinks)
	template = dontmanage.get_template("templates/includes/comments/comment.html")
	return template.render({"comment": comment.as_dict()})
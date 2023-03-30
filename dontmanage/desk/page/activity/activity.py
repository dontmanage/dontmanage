# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.core.doctype.activity_log.feed import get_feed_match_conditions
from dontmanage.utils import cint


@dontmanage.whitelist()
def get_feed(start, page_length):
	"""get feed"""
	match_conditions_communication = get_feed_match_conditions(dontmanage.session.user, "Communication")
	match_conditions_comment = get_feed_match_conditions(dontmanage.session.user, "Comment")

	result = dontmanage.db.sql(
		"""select X.*
		from (select name, owner, modified, creation, seen, comment_type,
				reference_doctype, reference_name, '' as link_doctype, '' as link_name, subject,
				communication_type, communication_medium, content
			from
				`tabCommunication`
			where
				communication_type = 'Communication'
				and communication_medium != 'Email'
				and {match_conditions_communication}
		UNION
			select name, owner, modified, creation, '0', 'Updated',
				reference_doctype, reference_name, link_doctype, link_name, subject,
				'Comment', '', content
			from
				`tabActivity Log`
		UNION
			select name, owner, modified, creation, '0', comment_type,
				reference_doctype, reference_name, link_doctype, link_name, '',
				'Comment', '', content
			from
				`tabComment`
			where
				{match_conditions_comment}
		) X
		order by X.creation DESC
		LIMIT %(page_length)s
		OFFSET %(start)s""".format(
			match_conditions_comment=match_conditions_comment,
			match_conditions_communication=match_conditions_communication,
		),
		{"user": dontmanage.session.user, "start": cint(start), "page_length": cint(page_length)},
		as_dict=True,
	)

	return result


@dontmanage.whitelist()
def get_heatmap_data():
	return dict(
		dontmanage.db.sql(
			"""select unix_timestamp(date(creation)), count(name)
		from `tabActivity Log`
		where
			date(creation) > subdate(curdate(), interval 1 year)
		group by date(creation)
		order by creation asc"""
		)
	)

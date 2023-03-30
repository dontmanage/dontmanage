import dontmanage


def execute():
	dontmanage.reload_doctype("Comment")

	if dontmanage.db.count("Feedback") > 20000:
		dontmanage.db.auto_commit_on_many_writes = True

	for feedback in dontmanage.get_all("Feedback", fields=["*"]):
		if feedback.like:
			new_comment = dontmanage.new_doc("Comment")
			new_comment.comment_type = "Like"
			new_comment.comment_email = feedback.owner
			new_comment.content = "Liked by: " + feedback.owner
			new_comment.reference_doctype = feedback.reference_doctype
			new_comment.reference_name = feedback.reference_name
			new_comment.creation = feedback.creation
			new_comment.modified = feedback.modified
			new_comment.owner = feedback.owner
			new_comment.modified_by = feedback.modified_by
			new_comment.ip_address = feedback.ip_address
			new_comment.db_insert()

	if dontmanage.db.auto_commit_on_many_writes:
		dontmanage.db.auto_commit_on_many_writes = False

	# clean up
	dontmanage.db.delete("Feedback")
	dontmanage.db.commit()

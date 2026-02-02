import dontmanage


# no context object is accepted
def get_context():
	context = dontmanage._dict()
	context.body = "Custom Content"
	return context

import dontmanage
import dontmanage.share


def execute():
	for user in dontmanage.STANDARD_USERS:
		dontmanage.share.remove("User", user, user)

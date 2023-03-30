# Copyright (c) 2021, DontManage and Contributors
# MIT License. See LICENSE

from dontmanage.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass

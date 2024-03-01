import dontmanage


class MaxFileSizeReachedError(dontmanage.ValidationError):
	pass


class FolderNotEmpty(dontmanage.ValidationError):
	pass


class FileTypeNotAllowed(dontmanage.ValidationError):
	pass


from dontmanage.exceptions import *

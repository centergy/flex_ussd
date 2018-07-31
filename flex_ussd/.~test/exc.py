
class TestPassportError(Exception):
	"""Error while handling an auth passport object(s)."""
	pass


class TestPassportWarning(Warning):
	"""A non blocking error while handling auth passport object(s)."""
	pass
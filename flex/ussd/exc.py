
class ImproperlyConfigured(Exception):
	"""Some component is somehow improperly configured."""
	pass



class ScreenNameError(ValueError):
	pass

class UssdNamespaceError(RuntimeError):
	pass
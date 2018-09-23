
class ImproperlyConfigured(Exception):
	"""Some component is somehow improperly configured."""
	pass



class ScreenMetadataError(ValueError):
	pass


class UssdNamespaceError(RuntimeError):
	pass

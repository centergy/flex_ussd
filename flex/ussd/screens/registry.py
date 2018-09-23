from flex.utils.decorators import export
from flex.utils.void import Void


@export
class ScreenRegistry(dict):
	__slots__ = ()

	def add(self, name, screen, *, silent=False):
		if name not in self:
			self[name] = screen
			return True
		elif not silent:
			raise KeyError('Screen name "%s" already exists.' % (name,))
		return False

	def get(self, screen, namespace=None, default=Void):
		from .core import UssdScreenMeta, UssdScreen

		if isinstance(screen, UssdScreenMeta):
			return screen

		if screen[0] == '.' and isinstance(namespace, (UssdScreenMeta, UssdScreen)):
			namespace = namespace.__meta__.namespace
			if namespace is None:
				screen = screen[1:]

		if screen[0] == '.':
			if not namespace or not isinstance(namespace, str):
				raise ValueError('Expected str or UssdScreen. got %r' % (type(namespace),))
			screen = '%s%s' % (namespace, screen)

		try:
			return self[screen]
		except KeyError:
			if default is Void:
				raise KeyError('UssdScreen "%s" not found' % (screen,))
			return default




screens = ScreenRegistry()

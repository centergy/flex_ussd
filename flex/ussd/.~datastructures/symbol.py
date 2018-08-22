
__all__ = [
	'symbol',
]


class _symbol(object):
	__slots__ = ('__name__', '__doc__')

	def __init__(self, name, doc=None):
		self.__name__ = name
		self.__doc__ = doc

	@property
	def name(self):
		return self.__name__

	def __reduce__(self):
		return symbol, (self.__name__, self.__doc__)

	def __str__(self):
		return self.__name__

	def __repr__(self):
		return 'symbol("%s")' % self.__name__

_symbol.__name__ = 'symbol'


class symbol(object):
	"""A constant symbol.

	>>> symbol('foo') is symbol('foo')
	True
	>>> symbol('foo')
	foo

	A slight refinement of the MAGICCOOKIE=object() pattern.  The primary
	advantage of symbol() is its str() and repr(). They are also singletons.

	Repeated calls of symbol('name') will all return the same instance.
	"""

	__slots__ = ()

	symbols = {}

	def __new__(cls, name, doc=None):
		try:
			return cls.symbols[name]
		except KeyError:
			return cls.symbols.setdefault(name, _symbol(name, doc))


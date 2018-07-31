
__all__ = [
	'VoidType', 'Void'
]




class VoidType(object):
	__slots__ = ()

	def __new__(cls):
		global __VOID_VALUE__
		if __VOID_VALUE__ is None:
			__VOID_VALUE__ = super(VoidType, cls).__new__(cls)
		return __VOID_VALUE__

	def __reduce__(self):
		return self.__class__, (),

	def __len__(self):
		return 0

	def __bool__(self):
		return False
	__nonzero__ = __bool__

	def __str__(self):
		return 'Void'

	def __repr__(self):
		return 'Void'


__VOID_VALUE__ = None

Void = VoidType()

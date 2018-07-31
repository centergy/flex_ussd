from threading import RLock
from warnings import warn

import sys
from ..datastructures import symbol

NOTHING = symbol('NOTHING')


class class_only_method(classmethod):
	"""Creates a classmethod available only to the class. Raises AttributeError
	when called from an instance of the class.
	"""

	__slots__ = ()

	def __init__(self, func, name=None):
		super(class_only_method, self).__init__(func)
		self.__name__ = name or func.__name__

	def __get__(self, obj, cls):
		if obj is not None:
			raise AttributeError('Class method {}.{}() is available only to '\
				'the class, and not it\'s instances.'\
				.format(cls.__name__, self.__name__))
		return super(class_only_method, self).__get__(obj, cls)


class class_property(classmethod):
	"""A decorator that converts a function into a lazy class property."""

	__slots__ = ()

	def __get__(self, obj, cls):
		func = super(class_property, self).__get__(obj, cls)
		return func()


class cached_class_property(class_property):
	"""A decorator that converts a function into a lazy class property."""

	def __init__(self, func, name=None, doc=None):
		super(cached_class_property, self).__init__(func)
		self.__name__ = name or func.__name__
		self.__module__ = func.__module__
		self.__doc__ = doc or func.__doc__
		self.lock = RLock()

	def __get__(self, obj, cls):
		with self.lock:
			rv = super(cached_class_property, self).__get__(obj, cls)
			setattr(cls, self.__name__, rv)
			return rv


class cached_property(property):
	"""A decorator that converts a function into a lazy property.  The
	function wrapped is called the first time to retrieve the result
	and then that calculated result is used the next time you access
	the value::

		class Foo(object):

			@cached_property
			def foo(self):
				# calculate something important here
				return 42

	The class has to have a `__dict__` in order for this property to
	work.
	"""

	# implementation detail: A subclass of python's builtin property
	# decorator, we override __get__ to check for a cached value. If one
	# choses to invoke __get__ by hand the property will still work as
	# expected because the lookup logic is replicated in __get__ for
	# manual invocation.

	def __init__(self, func, lock=False, name=None, doc=None):
		self.__name__ = name or func.__name__
		self.__module__ = func.__module__
		self.__doc__ = doc or func.__doc__
		self.func = func
		self.lock = (lock or None) and RLock()

	def __set__(self, obj, value):
		if self.lock is None:
			return self._set_value(obj, value)
		else:
			with self.lock:
				return self._set_value(obj, value)

	def __get__(self, obj, owner):
		if obj is None:
			return self
		if self.lock is None:
			return self._resolve(obj, owner)
		else:
			with self.lock:
				return self._resolve(obj, owner)

	def _set_value(self, obj, value):
		if _attr_is_sloted(obj.__class__, self.__name__):
			setattr(obj, self.__name__, value)
		else:
			obj.__dict__[self.__name__] = value

	def _resolve(self, obj, owner=None):
		if _attr_is_sloted(obj.__class__, self.__name__):
			# value = getattr(obj, self.__name__, NOTHING)
			# if value is NOTHING:
			# Commented this out as it might cause infinite recursion
			# TODO: Find out whether this causes any recursion.
			value = self.func(obj)
			setattr(obj, self.__name__, value)
		else:
			value = obj.__dict__.get(self.__name__, NOTHING)
			if value is NOTHING:
				value = obj.__dict__[self.__name__] = self.func(obj)
		return value



class locked_cached_property(cached_property):
	"""A decorator that converts a function into a lazy property.  The
	function wrapped is called the first time to retrieve the result
	and then that calculated result is used the next time you access
	the value.  Works like the one in Werkzeug but has a lock for
	thread safety.
	"""

	def __init__(self, func, name=None, doc=None):
		super(locked_cached_property, self).__init__(func, lock=True, name=name, doc=doc)

	# def __set__(self, instance, value):
	# 	with self.lock:
	# 		instance.__dict__[self.__name__] = value

	# def __get__(self, instance, type=None):
	# 	if instance is None:
	# 		return self

	# 	with self.lock:
	# 		value = instance.__dict__.get(self.__name__, NOTHING)
	# 		if value is NOTHING:
	# 			value = self.func(instance)
	# 			instance.__dict__[self.__name__] = value
	# 		return value



def export(obj, module=None, name=None):
	module = sys.modules[module or obj.__module__]
	ol = getattr(module, '__all__', None)
	if ol is None:
		ol = []
		setattr(module, '__all__', ol)
	ol.append(name or obj.__name__)
	return obj


def _attr_is_sloted(cls, attr):
	"""Check if given attribute is in the given class's __slots__.

	Checks recursively from the class to it's bases."""
	if not hasattr(cls, '__slots__'):
		return False

	if attr in cls.__slots__:
		return True

	for base in cls.__bases__:
		if base is not object and _attr_is_sloted(base, attr):
			return True

	return False
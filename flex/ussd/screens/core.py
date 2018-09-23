from logging import getLogger
from collections import OrderedDict


from .. import exc
from .registry import screens as registry
from .metadata import ScreenMetadata, get_metadata_class

logger = getLogger('ussd')



class StateAttribute(object):
	"""Defines a screen's state attribute."""
	__slots__ = ()



class UssdScreenMeta(type):

	def __new__(mcls, name, bases, dct):
		super_new = super(UssdScreenMeta, mcls).__new__

		# Pop defines meta
		raw_meta = dct.pop('Meta', None)

		# Gather screen's state attributes and pop them from dct
		_forbidden_state_attrs = frozenset(('app', 'request', 'session'))
		state_attrs = set()
		for k,v in dct.items():
			if isinstance(v, StateAttribute):
				if k in _forbidden_state_attrs:
					raise exc.ImproperlyConfigured(
						'Forbidden state attribute %s in screen %s.' % (k, name)
					)
				state_attrs.add(k)
				dct.pop(k)

		# if not any((b for b in bases if isinstance(b, UssdScreenMeta))):
		# 	return super_new(mcls, name, bases, dct)

		# Create class
		cls = super_new(mcls, name, bases, dct)

		# setup screen metadata.
		metadata_cls = get_metadata_class(cls, 'METADATA_CLASS', '__metadata_class__', set_final=True)
		metadata_cls(cls, '__meta__', raw_meta)

		# Add class to registry.
		if not cls.__meta__.abstract:
			try:
				registry.add(cls.__meta__.name, cls)
			except KeyError as e:
				raise exc.ImproperlyConfigured(
					'UssdScreen name conflict. %s in screen %s.%s.'\
					% (cls.__meta__.name, cls.__module__, name)
				) from e

		# Set own and inherited state attributes
		cls.__meta__.state_attributes |= state_attrs
		for b in bases:
			if isinstance(b, UssdScreenMeta):
				cls.__meta__.state_attributes |= b.__meta__.state_attributes

		return cls



class UssdScreen(object, metaclass=UssdScreenMeta):

	METADATA_CLASS = ScreenMetadata

	__meta__ = None

	request = None

	class Meta:
		abstract = True

	@property
	def app(self):
		return self.request.app

	@property
	def session(self):
		return self.request.session

	def init_request(self, request):
		self.request = request

	def get(self):
		return NotImplemented

	def put(self, *args):
		return NotImplemented

	def __getstate__(self):
		return {k: self.__dict__[k] for k in self.__meta__.state_attributes if k in self.__dict__}

	def __call__(self, *args):
		if args:
			return self.put(*args)
		else:
			return self.get()





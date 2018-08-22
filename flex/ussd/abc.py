import re
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import Sequence
from flex.utils.decorators import export


class ABC(object, metaclass=ABCMeta):
	__slots__ = ()


@export
class AppBoundInstanceABC(ABC):
	__slots__ = ()

	def __init__(self, app=None):
		if app is not None:
			self.init_app(app)

	@abstractmethod
	def init_app(self, app):
		pass



@export
class CacheBackendABC(AppBoundInstanceABC):

	__slots__ = ()

	@abstractmethod
	def get(self, key):
		raise NotImplementedError('%s.get' % self.__class__.__name__)

	@abstractmethod
	def set(self, key, value, timeout=None):
		raise NotImplementedError('%s.set' % self.__class__.__name__)

	@abstractmethod
	def delete(self, key):
		raise NotImplementedError('%s.delete' % self.__class__.__name__)

	@abstractmethod
	def expire(self, key, timeout):
		raise NotImplementedError('%s.expire' % self.__class__.__name__)



@export
class SessionManagerABC(ABC):
	__slots__ = ()

	@abstractmethod
	def open(self, app, request):
		raise NotImplementedError('%s.open' % self.__class__.__name__)

	@abstractmethod
	def close(self, app, session, response):
		raise NotImplementedError('%s.close' % self.__class__.__name__)



@export
class UssdDataSequence(Sequence):

	__slots__ = ()

	_arg_splitter = re.compile(r'\*(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)')

	@property
	@abstractmethod
	def ussd_data(self) -> list:
		pass

	def as_str(self):
		ln = len(self.ussd_data)
		return '' if ln == 0 else str(self.ussd_data[0]) if ln == 1	else '*'.join(self)

	def parse_ussd_data(self, value):
		if isinstance(value, str):
			return (re.sub(r'^\"(.*)\"$', r'\1', str(c)) for c in self._arg_splitter.split(value))
		return value

	@abstractmethod
	def copy(self):
		return self.__class__(self.ussd_data)

	def equals(self, other):
		"""Check equality against strings, lists and tuples.
		"""
		if isinstance(other, UssdDataSequence):
			return self.ussd_data == other.ussd_data
		else:
			try:
				other = self.parse_ussd_data(other)
				if not isinstance(other, list):
					other = list(other)
			except (TypeError, ValueError):
				return False
		return self.ussd_data == other

	def startswith(self, other, start=None, end=None):
		if isinstance(other, UssdDataSequence):
			other = other.ussd_data
		else:
			other = self.parse_ussd_data(other)
			if not isinstance(other, list):
				other = list(other)

		target = self.ussd_data if start is None and end is None else self.ussd_data[start:end]
		olen, tlen = len(other), len(target)
		if tlen == olen:
			return target == other
		elif tlen > olen:
			return target[:olen] == other
		else:
			return False

	def endswith(self, other, start=None, end=None):
		if isinstance(other, UssdDataSequence):
			other = other.ussd_data
		else:
			other = self.parse_ussd_data(other)
			if not isinstance(other, list):
				other = list(other)

		target = self.ussd_data if start is None and end is None else self.ussd_data[start:end]
		olen, tlen = len(other), len(target)
		if tlen == olen:
			return target == other
		elif tlen > olen:
			return target[(olen*-1):] == other
		else:
			return False

	def __contains__(self, value):
		if isinstance(value, UssdDataSequence):
			value = value.as_str()
		else:
			value = '*'.join(self.parse_ussd_data(value))
		return value in self.as_str()

	def __eq__(self, other):
		if isinstance(other, UssdDataSequence):
			return self.equals(other)
		else:
			return NotImplemented

	def __ne__(self, other):
		if isinstance(other, UssdDataSequence):
			return not self.equals(other)
		else:
			return NotImplemented

	def __str__(self):
		return self.as_str()



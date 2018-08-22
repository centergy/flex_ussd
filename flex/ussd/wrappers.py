import re
from enum import Enum
from collections import UserList

from flex.utils.decorators import export

from .abc import UssdDataSequence


NOTHING = object()

@export
class UssdStatus(Enum):
	CON = 'CON'
	END = 'END'



@export
class UssdData(UssdDataSequence, UserList):
	"""A chunk of ussd data with sequence capabilities.

	NB: Might be dropped in favor of views.
	"""

	__slots__ = ('name',)

	def __init__(self, data=None, name=None):
		super(UssdData, self).__init__(self.parse_ussd_data(data))
		self.name = data.name if name is None and isinstance(data, UssdData) else name
		self.as_str()

	@property
	def ussd_data(self):
		return self.data

	def copy(self):
		return self.__class__(self.data, self.name)

	# def __eq__(self, other):
	# 	if isinstance(other, UssdDataChunk):
	# 		return other.name == self.name and other.data == self.data
	# 	elif self.name is None and isinstance(other, list):
	# 		return self.data == other
	# 	else:
	# 		return False

	# def __ne__(self, other):
	# 	return not self.__eq__(other)

	def __repr__(self):
		return '%s(data="%s")' % (self.__class__.__name__, self,)


UssdCode = export(UssdData, name='UssdCode')




@export
class UssdDataStack(UssdDataSequence):
	"""Base class for USSD argument vetors.
	"""
	__slots__ = ('data',)

	def __init__(self, d):
		self.data = list(self.parse_ussd_data(c) for c in ((d,) if isinstance(d, str) else d or [()]))

	@property
	def ussd_data(self):
		return list(self)

	def get(self, name, default=None):
		try:
			return self[name]
		except KeyError:
			return default

	def copy(self):
		return self.__class__(self.data)

	def __getitem_custom__(self, key):
		if isinstance(key, int):
			_key = key
			sign = -1 if key < 0 else 1
			for ci in (range(-1, -(len(self.data)+1), -1) if key < 0 else range(len(self.data))):
				chunk = self.data[ci]
				lchunck = len(chunk)
				if lchunck > key*sign or (sign == -1 and lchunck == key*sign):
					return chunk[key]
				else:
					key = key - lchunck*sign
			raise KeyError(_key)

	def __getitem__(self, key):
		if key is None or isinstance(key, str):
			for chunk in self.data:
				if key == chunk.name:
					return chunk
			raise KeyError('No chunk named %s.' % (key,))
		else:
			return list(self).__getitem__(key)

	def __len__(self):
		sum((len(c) for c in self.data))

	def __iter__(self):
		for chunk in self.data:
			yield from chunk

	# def __eq__(self, other):
	# 	if isinstance(other, UssdDataStack):
	# 		return self.data.__eq__(other.data)
	# 	return False

	# def __ne__(self, other):
	# 	return not self.__eq__(other)

	def __repr__(self):
		return '%s("%s")' % (self.__class__.__name__, self.data)


@export
class UssdRequestData(UssdDataStack):
	"""The USSD request data.

	TODO:
		Use views to define partitions and slices instead of partitioning the
		data into nested chunks. Chunking makes some operations like len(),
		iter() e.t.c more expensive.

	Attributes:
		data: A list representing the USSD request data.data
		head: The top most unpartitioned chunk of the data.
	"""

	__slots__ = ()

	def __init__(self, d):
		self.data = list(UssdData(c) for c in ((d,) if isinstance(d, str) else d or [()]))
		self.data[-1].name = 'head'

	@property
	def head(self):
		return self.data[-1]

	def partition(self, chunk, name=None):
		if isinstance(chunk, (str, list, tuple, UssdData)):
			chunk = UssdData(chunk)
			if not self.head.startswith(chunk):
				raise ValueError('Shift value must be a prefix of argv head.')
			ln = len(chunk)
		elif isinstance(chunk, int):
			ln = chunk
			chunk = UssdData(self.head[:ln])

		if name is not None and (name == 'head' or not isinstance(name, str)):
			raise ValueError('Partition name must be any str other than "head" or None.')

		if chunk is not None:
			self.head[:ln] = []
			chunk.name = name
		return chunk

	def __getitem__(self, key):
		return self.head if key == 'head' else super(UssdRequestData, self).__getitem__(key)



@export
class UssdRequest(object):
	"""A basic USSD request
	"""
	def __init__(self, phone_number, session_id=None, ussd_string=None, service_code='', initial_code='', http_request=None):
		self.app = None
		self.session = None
		self.phone_number = phone_number
		self.session_id = session_id
		self.http_request = http_request

		ussd_string = ussd_string or ''
		if initial_code and ussd_string != initial_code and not ussd_string.startswith(initial_code+'*'):
			ussd_string = initial_code + '*' + ussd_string if ussd_string else initial_code

		if service_code:
			ussd_string = service_code + '*' + ussd_string if ussd_string else service_code

		self.data = UssdRequestData([ussd_string,])
		self.data.partition(service_code or '', 'service_code')
		if initial_code:
			self.data.partition(initial_code, 'initial_code')

	@property
	def service_code(self):
		return self.data['service_code']






@export
class UssdResponse(object):

	def __init__(self, payload, status=UssdStatus.CON):
		self.payload = payload
		self.status = status
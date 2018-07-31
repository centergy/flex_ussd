import os
import re
import string
import random
import pickle
import warnings
from django.apps import apps
from collections import namedtuple
from django.conf import settings
from django.core.cache import cache
from collections import OrderedDict
from logging import getLogger

from ..datastructures import ClassReigistry, AttributeBag, choice, symbol
from ..utils.decorators import cached_property, class_property
from ..settings import ussd_settings

from .options import screen_meta_option, ScreenMetaOptions


logger = getLogger('ussd')



class BaseRegistryScreenBackend(object):
	"""docstring for ScreenUIDBackend"""

	def has(self, screen):
		pass

	def get_id(self, screen):
		pass

	def generate_id(self, screen):
		r

	def set_id(self, screen):
		screen._meta.id = self.get_id(screen) or


NOTHING = symbol('NOTHING')

_REGISTRY = ClassReigistry()

_UID_LEN = ussd_settings.SCREEN_UID_LEN



_UID_LOCK = set()
_UID_LOCK_FILE = os.path.join(settings.LOCAL_DATA_DIR, '.ussd-screens-uid.lock')
if os.path.exists(_UID_LOCK_FILE):
	with open(_UID_LOCK_FILE, 'r') as fo:
		_UID_LOCK = set((k.strip() for k in fo.read().split('\n') if k.strip()))


def _save_uid_lock():
	with open(_UID_LOCK_FILE, 'w+') as fo:
		fo.write('\n'.join(_UID_LOCK))


_UID_MAP =  ClassReigistry()
_UID_MAP_FILE = os.path.join(settings.LOCAL_DATA_DIR, '.ussd-screens-uid.map')
if os.path.exists(_UID_MAP_FILE):
	with open(_UID_MAP_FILE, 'rb') as mp:
		_UID_MAP = pickle.load(mp)


def _save_uid_map():
	with open(_UID_MAP_FILE, 'wb+') as fo:
		pickle.dump(_UID_MAP, fo)


def _generate_screen_uid():
	rv, i = None, 0
	while rv is None or rv in _UID_LOCK or rv in _REGISTRY:
		i += 1
		rv = ''.join(random.choice(string.digits + string.ascii_lowercase)\
				for _ in range(max((i/100,2))))
	_UID_LOCK.add(rv)
	_save_uid_lock()
	return rv


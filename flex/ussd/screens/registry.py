from threading import Lock
from ..config import config


class ScreenRegistry(object):
	__slots__ = ('_lock', 'ready', 'backend', 'screens')

	def __init__(self, backend=None):
		self._lock = Lock()
		self.ready = False
		self.backend = backend

	def set_backend(self, backend):
		pass

	def _(self):
		pass



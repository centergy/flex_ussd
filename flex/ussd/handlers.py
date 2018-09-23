from typing import Callable, Any

from functools import wraps
from flex.utils.decorators import cached_property
from flex.utils.module_loading import import_if_string, import_strings

from .abc import AppBoundInstanceABC
from .wrappers import UssdRequest
from .response import BaseUssdResponse, UssdResponse, UssdStatus
from .screens import screens, UssdScreen
from . import signals


class RequestHandler(AppBoundInstanceABC):

	def __init__(self, app=None):
		self.app = None
		self._exception_middleware = []
		if app is not None:
			self.init_app(app)

	@cached_property
	def handle(self):
		return self.create_handler()

	def init_app(self, app):
		if self.app and app is not self.app:
			raise RuntimeError(
				'Error binding app %s to %s. Already bound to %s'\
				% (app.name, self.__class__.__name__, self.app.name)
			)
		self.app = app

	def get_middleware(self):
		return self.app.middleware

	def create_handler(self) -> Callable[[UssdRequest], BaseUssdResponse]:
		self._exception_middleware = []
		handler = self.wrap_exception_handler(self.screen_handler, self.get_exception_handler(0))
		for mware in self.get_middleware():
			mw_instance = mware(handler)
			if mw_instance is not None:
				if hasattr(mw_instance, 'process_exception'):
					self._exception_middleware.append(mw_instance.process_exception)

				handler = self.wrap_exception_handler(
					mw_instance,
					self.get_exception_handler(len(self._exception_middleware))
				)
		return handler

	def before_request(self, request) -> None:
		signals.before_request.send(self.app, request=request)

	def after_request(self, response, request) -> None:
		signals.after_request.send(self.app, response=response, request=request)

	def get_initial_screen(self) -> UssdScreen:
		rv = screens.get(self.app.initial_screen)
		return rv()

	def screen_handler(self, request) -> BaseUssdResponse:
		screen = request.session.screen or self.get_initial_screen()
		rv = self.dispatch_to_screen(screen, request, *request.data.head)
		return rv

	def dispatch_to_screen(self, screen: UssdScreen, request: UssdRequest, arg=None, *next_args) -> UssdResponse:
		request.session.screen = screen

		screen.init_request(request)

		res = screen() if arg is None else screen(arg)

		if isinstance(res, BaseUssdResponse):
			if res.status == UssdStatus.REDIRECT:
				next_screen = screens.get(res.screen, screen)(**res.params)
				if res.data:
					next_args = res.data
				return self.dispatch_to_screen(next_screen, request, *next_args)
			else:
				return res
		elif isinstance(res, str):
			return UssdResponse(res)

		raise RuntimeError(
			'Screen must return a BaseUssdResponse object or string. Got %s' % (type(res),)
		)

	def wrap_exception_handler(self, func, exception_handler=None):
		"""Wrap the given callable in exception-to-response conversion.
		"""
		exception_handler = exception_handler or self.get_exception_response
		@wraps(func)
		def inner(request):
			try:
				return func(request)
			except Exception as exc:
				return exception_handler(request, exc)
		return inner

	def get_exception_handler(self, depth=0):
		def exception_handler(request, exception):
			for handler in self._exception_middleware[depth:]:
				response = handler(request, exception)
				if response:
					return response
			return self.get_exception_response(request, exception)
		return exception_handler

	def get_exception_response(self, request, exc):
		raise exc

	def __call__(self, request: UssdRequest):
		request.app = self.app
		self.before_request(request)
		response = self.handle(request)
		self.after_request(response, request)
		return response







import re

from .backends import ussd_session_backend
from .config import config
from .utils import ArgumentVector


class UssdMiddleware(object):

	def __init__(self, get_response):
		self.get_response = get_response

	@property
	def backend(self):
		return ussd_session_backend

	def validate_request(self, request, url):
		if request.method not in url['methods']:
			raise ValueError(
				'Http Method %s not allowed for USSD endpoint %s.'\
				% (request.method, request.path)
			)
		for k in ('service_code', 'ussd_string', 'msisdn', 'session_id'):
			if k not in request.GET:
				raise ValueError('Query param %s required in USSD requests.' % k)

	def is_ussd_request(self, request):
		for url in config.URLS:
			if re.search(url['path'], request.path) is not None:
				self.validate_request(request, url)
				# print(request.path, 'is a ussd request. Matched:', url['path'])
				return True

		# print(request.path, 'is not a ussd request. URLs:', config.URLS)
		return False

	def open_session(self, req):
		session = self.backend.open_session(req)
		req.ussd_session = session
		# print('USSD session: %s' % (session.key,))
		# print('  - Created  :', session.created_at.isoformat())
		# print('  - Accessed :', session.accessed_at and session.accessed_at.isoformat())
		# print('  - Is New   :', session.is_new)
		# print('  - Started  :', getattr(session, '_is_started', False))

	def close_session(self, req, response):
		if hasattr(req, 'ussd_session'):
			self.backend.close_session(req.ussd_session, req, response)
			# session = req.ussd_session
			# print(' Closing USSD session: %s' % (session.key,))

	def prepare_request(self, request):
		service_code = request.GET['service_code']
		base_code = request.GET.get('initial_code')
		argstr = request.GET['ussd_string']

		argv = ArgumentVector(service_code, argstr, base_code)
		request.service_code = service_code

		session = request.ussd_session
		xargv = session.argv

		request.args = argv - xargv if xargv else []

		#TODO:- argv might not be needed in the request object. DONE.
		session.argv = argv

		# print(' Ussd argv  	: %r' % (argv,))
		# print(' Ussd xargv 	: %r' % (xargv,))
		# print(' Ussd inputs :', request.args)

	def __call__(self, req):
		# print('-'*140)
		from time import time
		st = time()
		print('[REQUEST START]')

		is_ussd_request = self.is_ussd_request(req)
		if is_ussd_request:
			self.open_session(req)
			self.prepare_request(req)

		response = self.get_response(req)

		if is_ussd_request:
			self.close_session(req, response)

		print('[REQUEST END] time:', time()-st, '\n')

		# print('-'*140)
		# print('')

		return response



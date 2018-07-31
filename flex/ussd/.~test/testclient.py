from .auth import get_superuser, get_auth_client, get_request_token, get_access_token, parse_superuser
from client.tokens.models import Request as RequestTokenModel, Access as AccessTokenModel
from .utils import validate_response_json, validate_response_status_code, get_my_public_ip
from passport.models import Passport as PassportModel
from .passports import get_passport, parse_passport
from django.test import client as dj_test_client
from client.models import Client as AuthClientModel
from django.contrib.auth import get_user_model
from django.utils.functional import curry
from collections import defaultdict


class RequestFactory(dj_test_client.RequestFactory):

	ACCESS_TOKEN = 'access'
	REQUEST_TOKEN = 'request'
	CLIENT_TOKEN = 'client'

	auth_token_names = frozenset(('access', 'request', 'client'))

	environ_dirt = frozenset((
		'superuser', 'token', 'me', 'auth_header', 'auth'))

	def __init__(self, **defaults):
		super(RequestFactory, self).__init__(**defaults)
		self.token_cache = defaultdict(dict)

	def remote_ip(self, ip=None):
		self.defaults['REMOTE_ADDR'] = ip or get_my_public_ip() or '127.0.0.1'
		return self

	def _base_environ(self, **request):
		environ = super(RequestFactory, self)._base_environ(**request)
		environ['HTTP_AUTHORIZATION'] = self._get_auth_header(environ)
		return self._clean_environ(environ)

	def _clean_environ(self, environ):
		for k in self.environ_dirt:
			environ.pop(k, None)
		return environ

	def _get_auth_header(self, environ):
		"""get the Authorization header for the request."""
		header = environ.get('auth_header', environ.get('auth'))
		if header is None or str(header) in self.auth_token_names:
			token = header or str(environ.get('token', self.ACCESS_TOKEN))
			if token == self.CLIENT_TOKEN:
				header = self._get_auth_client(environ).auth_header()
			elif token == self.REQUEST_TOKEN:
				header = self._get_request_token(environ).auth_header()
			elif token == self.ACCESS_TOKEN:
				header = self._get_access_token(environ).auth_header()
			else:
				raise ValueError('Invalid auth token type: {}. '\
					'Allowed values: Client.ACCESS_TOKEN, Client.REQUEST_TOKEN '\
					'or Client.CLIENT_TOKEN.'.format(token))
		return str(header)

	def _get_superuser(self, environ):
		user = parse_superuser(environ.get('superuser'), {})
		if user and isinstance(user, get_user_model()):
			return user
		return get_superuser(**user)

	def _get_auth_client(self, environ):
		user = self._get_superuser(environ)
		client = self.token_cache[self.CLIENT_TOKEN].get(user)
		if client:
			return client
		rv = self.token_cache[self.CLIENT_TOKEN][user] = get_auth_client(user)
		return rv

	def _get_request_token(self, environ):
		client = self._get_auth_client(environ)
		request = self.token_cache[self.REQUEST_TOKEN].get(client)
		if request:
			return request
		rv = self.token_cache[self.REQUEST_TOKEN][client] = get_request_token(client)
		return rv

	def _get_access_token(self, environ):
		me = self._get_passport(environ)
		access = self.token_cache[self.ACCESS_TOKEN].get(me.who)
		if access:
			return access
		request = self._get_request_token(environ)
		rv = get_access_token(passport=me, request=request)
		self.token_cache[self.ACCESS_TOKEN][me.who] = rv
		return rv

	def _get_passport(self, environ):
		me = parse_passport(environ.get('me'), {})
		if me and isinstance(me, PassportModel):
			return me
		return get_passport(**me)



class Client(RequestFactory, dj_test_client.Client):

	def request(self, **request):
		response = super(Client, self).request(**request)
		if response:
			response.validate = curry(self._validate_response, response)
		return response

	def _validate_response(self, response, status_code=200, redirect=False, **extra):
		if status_code:
			validate_response_status_code(response.status_code, status_code, redirect)

		if 'application/json' in response.get('Content-Type'):
			validate_response_json(response.json(), **extra)


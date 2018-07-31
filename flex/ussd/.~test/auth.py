from client.tokens.models import Request as RequestTokenModel, Access as AccessTokenModel
from .passports import PassportModel, parse_passport
from client.models import Client as AuthClientModel
from django.contrib.auth import get_user_model
from six import string_types, integer_types
from .passports import get_passport
from django.conf import settings
from . import exc, const
import urllib
import base64


class AuthHeader(dict):
	""""""
	encoders = [
		(urllib.urlencode, 1),
		(base64.b64encode, 2)
	]

	def __str__(self):
		value = self
		for func, rounds in self.encoders:
			for r in range(rounds):
				value = func(value)
		return value


def get_superuser(username=None, email=None, password=None, **extra_fields):
	"""Get the Django test admin user. Creates a new one if user doesn't exist.

	The field values used to fetch and create the user can be set on the
	TEST_SUPER_USER settings variable as a dict.

	Default field values::
		TEST_SUPER_USER = {
			'username' : 'admin',
			'password' : 'password',
			'email' : 'admin@example.com'
		}
	"""
	data = dict(
			username='admin',
			password='password',
			email='admin@example.com'
		)
	data.update(const.TEST_SUPER_USER)
	data.update(getattr(settings, 'TEST_SUPER_USER', {}))

	if username is not None:
		data['username'] = username
	if email is not None:
		data['email'] = email
	if password is not None:
		data['password'] = password

	data.update(extra_fields)

	User = get_user_model()
	username = data.get(User.USERNAME_FIELD, data.pop('username'))

	try:
		user = User._default_manager.get(**{User.USERNAME_FIELD: username})
	except User.DoesNotExist:
		password = data.pop('password')
		email = data.pop('email')
		user = User._default_manager.create_superuser(
						username, email, password, **data)

	return user


def get_auth_client(user=None):
	"""Get the :class:`client.models.Client` instance for the given superuser.

	If user is not given, the default superuser is used (see: :func:`get_superuser`).
	If the given superuser does not have a client, a new one is created.

	:param user: A superuser instance or username. If not given the default superuser
		from :func:`get_superuser` is used.
	:type user: django.contrib.auth.models.User or string, optional
	"""
	if not isinstance(user, get_user_model()):
		user = get_superuser(**parse_superuser(user, {}))

	manager = AuthClientModel._default_manager

	client = manager.filter(user__pk=user.pk).first()
	if client is None:
		name = 'test_client_{}'.format(user.pk)
		description = 'Test Client Fixture'
		client = manager.create_client(user, name, description)

	return client


def get_request_token(client=None, user=None):
	"""Get a :class:`client.tokens.models.Request` instance.

	Creates a request token instance for the given client or user's client.
	"""
	if client is None:
		client = get_auth_client(user)
	return RequestTokenModel._default_manager.create_request(client)


def get_access_token(passport=None, request=None, client=None, user=None):
	"""Get an :class:`client.tokens.models.Access` instance.

	Creates an access token instance for the given passport and request, client
	or user.
	"""
	if not isinstance(passport, PassportModel):
		passport = get_passport(**parse_passport(passport, {}))

	if request is None:
		request = get_request_token(client, user)

	if client is None:
		client = request.client

	assert request.client == client

	access = AccessTokenModel.objects.create_access(request, passport, client)
	return access


def parse_superuser(admin_user, default=None):
	"""Try parsing the given object into the correct format for use in get_superuser().

	If the object fails the truth test, the default is returned.
	"""
	if admin_user:
		if isinstance(admin_user, string_types):
			return dict(username=admin_user)
		elif isinstance(admin_user, (list, tuple)):
			return dict(**admin_user)

	return admin_user or default
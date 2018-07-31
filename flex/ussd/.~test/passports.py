from passport.models import clean_username, clean_phone_number
from passport.models import Passport as PassportModel
from six import string_types, integer_types
from django.conf import settings
from warnings import warn
from . import exc, const
import re

def get_passport(username=None, phone_number=None, password=None, who=None, **extra_fields):
	defaults = dict(
			username='test',
			phone_number='+25470000000000',
			password='password'
		)
	defaults.update(const.TEST_PASSPORT)
	defaults.update(getattr(settings, 'TEST_PASSPORT', {}))

	data = dict(
			who=who,
			username=username,
			password=password,
			phone_number=phone_number
		)

	if username == phone_number == who == None:
		data['who'] = defaults.get('who')

	who = data.get('who')
	username = data.get('username')
	phone_number = data.get('phone_number')
	manager = PassportModel.objects

	if who:
		passport = manager.get_user_by_id(who)
	else:
		if username:
			passport = manager.get_user(username)
		elif phone_number:
			passport = manager.get_user_by_phone_number(phone_number)
		else:
			username = defaults['username']
			phone_number = defaults['phone_number']
			passport = manager.get_user(username)
			if passport is None:
				passport = manager.get_user_by_phone_number(phone_number)

		if passport is None and username and phone_number:
			password = data.get('password') or defaults['password']
			passport = manager.create_user(username, password, phone_number)

			# Update the model with extra_fields if they were provided,
			if extra_fields:
				for k in extra_fields.keys():
					setattr(passport, k, extra_fields[k])
				passport.save()


	if passport is None:
		raise exc.TestPassportError(
			'Unable fetch or create passport with: '\
			'username="{}", phone_number="{}" and who="{}".'\
			.format(username, phone_number, who))
	else:
		if username and passport.username != clean_username(username):
			warn(
				'The username for fetched passport does not match '\
					'expected value. Expected: "{}" but got: "{}".'\
					.format(clean_username(username), passport.username),
				category=exc.TestPassportWarning
			)

		if phone_number and passport.phone_number != clean_phone_number(phone_number):
			warn(
				'The phone_number for fetched passport does not match '\
					'expected value. Expected: "{}" but got: "{}".'\
					.format(clean_phone_number(phone_number),
						passport.phone_number
					),
				category=exc.TestPassportWarning
			)

	return passport


_re_phone_number = re.compile(r'^\+?[ 0-9]{9,15}\Z')

def _is_phone_number(value):
	"""Determine whether the given str value matches a phone number."""
	return bool(_re_phone_number.search(value.strip()))


_re_who = re.compile(r'^[a-z]{3}[a-z0-9]{30}[0-9a-fA-F]{32}$')

def _is_who_str(value):
	value = value.strip()
	return len(value) == 65 and bool(_re_who.search(value))


def parse_passport(passport, default=None):
	"""Try parsing the given object into the correct format for use in get_auth_passport().

	If the object fails the truth test, the default is returned.
	"""
	if passport:
		if isinstance(passport, string_types):
			if _is_who_str(passport):
				return dict(who=passport)
			elif _is_phone_number(passport):
				return dict(phone_number=passport)
			else:
				return dict(username=passport)
		elif isinstance(passport, (list, tuple)):
			return dict(**passport)

	return passport or default

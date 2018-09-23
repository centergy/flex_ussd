from enum import IntEnum
from flex.utils.decorators import export


@export
class UssdStatus(IntEnum):
	CON = 0
	END = 1
	REDIRECT = 2


@export
class BaseUssdResponse(object):
	status = UssdStatus.CON


@export
class UssdResponse(BaseUssdResponse):
	"""UssdResponse object."""

	def __init__(self, data=None, status=None):
		self.data = data
		if status is not None:
			self.status = status


@export
class UssdRedirectResponse(BaseUssdResponse):
	"""UssdRedirectResponse object."""

	status = UssdStatus.REDIRECT

	def __init__(self, __ussd_screen, __ussd_data=None, **params):
		self.screen = __ussd_screen
		self.data = __ussd_data or ()
		self.params = params

redirect = UssdRedirectResponse
export(redirect, name='redirect')


import pytest
from flex.ussd.screens import screens
from .screens import Home


xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


class ScreenRegistryTest(object):

	def test_init(self):
		assert screens.get('test.home') is Home

	def test_meta(self):
		for f in Home.__meta__.__fields__:
			print(f , ' --> ', getattr(Home.__meta__, f))
		assert False


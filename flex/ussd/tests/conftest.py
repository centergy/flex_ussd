import pytest
from ..test.monkeypatches import *
from ..test.fixtures import *


import pytest
def pytest_addoption(parser):
	parser.addoption("--slow", action="store_true",
					 default=False, help="run slow tests")
	parser.addoption("--speed", action="store_true",
					 default=False, help="run speed tests")

def pytest_collection_modifyitems(config, items):
	run_speed = config.getoption('--speed')
	run_slow = config.getoption("--slow")

	skip_slow = pytest.mark.skip(reason="need --slow option to run")
	skip_speed = pytest.mark.skip(reason="need --speed option to run")
	skip_none_speed = pytest.mark.skip(reason="not a speed test.")
	for item in items:
		if run_speed and "speedtest" not in item.keywords:
			item.add_marker(skip_none_speed)
		elif not run_speed and "speedtest" in item.keywords:
			item.add_marker(skip_speed)
		elif not run_slow and "slow" in item.keywords:
			item.add_marker(skip_slow)
import re


def to_snakecase(val):
	val = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', val)
	val = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', val).lower()
	val = re.sub(r'[^0-9a-z_]+', '_', val)
	return  val  #re.sub(r'(.)_screen$', r'\1', val)


def to_startcase(val):
	return re.sub(r'_+', ' ', to_snakecase(val)).title()

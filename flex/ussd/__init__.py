from .namespaces import ussd_namespace



default_app_config = 'ussd.apps.UssdConfig'


def get_screen(name, *args, **kwargs):
	from .screens import get_screen
	return get_screen(name, *args, **kwargs)

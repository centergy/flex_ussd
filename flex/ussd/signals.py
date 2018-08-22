from flex.signal import Namespace

signals = Namespace('flex.ussd')


def _get_app_name(app):
	return app if isinstance(app, str) else getattr(app, 'name', app)


""" Pipelines
"""
# Global config
configure 				= signals.pipeline('configure')

cache_backend_factory 	= signals.pipeline('cache_backend_factory').configure(get_sender_id=_get_app_name)
session_manager_factory = signals.pipeline('session_manager_factory').configure(get_sender_id=_get_app_name)
request_handler_factory = signals.pipeline('request_handler_factory').configure(get_sender_id=_get_app_name)
middleware_list 		= signals.pipeline('middleware_list').configure(get_sender_id=_get_app_name)
# Application configuration
app_config 				= signals.pipeline('app_config').configure(get_sender_id=_get_app_name)
#
open_session 			= signals.pipeline('open_session').configure(get_sender_id=_get_app_name)
save_session 			= signals.pipeline('save_session').configure(get_sender_id=_get_app_name)
#
before_request 			= signals.pipeline('before_request').configure(get_sender_id=_get_app_name)
after_request 			= signals.pipeline('after_request').configure(get_sender_id=_get_app_name)


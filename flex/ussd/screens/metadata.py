import re
from flex.utils import text
from flex.utils.void import Void
from flex.utils.decorators import export
from flex.utils.metadata import BaseMetadata, metafield, get_metadata_class

from .. import exc
from ..namespaces import module_ussd_namespace, isvalid_namespace_name

__all__ = [
	'metafield', 'get_metadata_class',
]



@export
class ScreenMetadata(BaseMetadata):

	abstract = metafield(default=False)

	@property
	def screen(self):
		return self.target

	@metafield()
	def label(self, value):
		return value or text.startcase(str(self.name).rpartition('.')[2])

	@metafield()
	def description(self, value):
		return value or self.target.__doc__

	@metafield()
	def name(self, value):
		if self.abstract:
			return value

		value = value or text.snake(self.target.__name__)

		if not isvalid_namespace_name(value, split=False):
			raise exc.ScreenMetadataError(
				'Invalid UssdScreen name <%s.%s(name="%s")>.'\
				% (self.target.__module__, self.target.__name__, value)
			)

		return '%s.%s' % (self.namespace, value,) if self.namespace else value

	@metafield(default=Void)
	def namespace(self, value):
		if self.abstract:
			return None

		if value is Void:
			try:
				value = module_ussd_namespace(self.target.__module__)
			except exc.UssdNamespaceError as e:
				raise exc.ScreenMetadataError(
					'Invalid UssdScreen namespace %s in <%s.%s>.'\
					% (value, self.target.__module__, self.target.__name__)
				) from e
		elif value is not None and not isvalid_namespace_name(value):
			raise exc.ScreenMetadataError(
				'Invalid UssdScreen namespace %s in <%s.%s>.'\
				% (value, self.target.__module__, self.target.__name__)
			)
		return value

	@metafield()
	def state_attributes(self, value):
		return set()


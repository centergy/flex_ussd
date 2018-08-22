from flex.utils.decorators import export


@export
class ScreenRegistry(dict):
	__slots__ = ()



registry = ScreenRegistry()

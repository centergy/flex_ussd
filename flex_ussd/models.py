from django.db import models
from .screens import get_screen

class ScreenManager(models.Manager):
	pass



class Screen(models.Model):
	name = models.CharField(max_length=100, unique=True)
	verbose_name = models.CharField(max_length=100)

	objects = ScreenManager()

	@property
	def cls(self):
		return self.name and get_screen(self.name) or None




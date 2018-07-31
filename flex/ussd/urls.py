
from django.conf.urls import url
from .views import UssdView


urlpatterns=[
	url(r'^$', UssdView.as_view(), name='ussd'),
]
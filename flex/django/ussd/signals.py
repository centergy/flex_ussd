from django.dispatch import Signal

ussd_screen_enter = Signal(providing_args=['session',])
from django.urls import path
from .forgot_password_views import (
    forgot_password,
    forgot_password_done,
    reset_password,
    reset_password_complete,
)

urlpatterns = [
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('forgot-password/done/', forgot_password_done, name='forgot_password_done'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),
    path('reset-password/done/', reset_password_complete, name='reset_password_complete'),
]

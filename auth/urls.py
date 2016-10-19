from __future__ import unicode_literals

from django.conf.urls import url

import auth.views

urlpatterns = [
    url(r'^login/', auth.views.jwt_login, name='login'),
    url(r'^info/', auth.views.info, name='info'),
    url(r'^refresh/', auth.views.refresh, name='refresh'),
]

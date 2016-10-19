from django.conf.urls import include, url

import auth.urls
import cas.views

urlpatterns = [
    url(r'^$', cas.views.index, name='home'),
    url(r'^auth/', include(auth.urls)),
]

from django.conf.urls import url, include

from orders_app.api import v1_api

urlpatterns = [
    url(r'^api/', include(v1_api.urls))
]
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from orders_app.models import CustomUser, Store, Item

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Store)
admin.site.register(Item)
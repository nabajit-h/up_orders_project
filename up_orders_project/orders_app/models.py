# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# Custom user
class CustomUser(models.Model):
    ROLE_CHOICES =[
        ('Consumer', 'Consumer'),
        ('Merchant', 'Merchant'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.name
    
# Store belongs to a Merchant
class Store(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=150, null=True)
    merchant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ' ' + self.address

# Item belongs to a store
class Item(models.Model):
    CATEGORY_CHOICES = (
        ('Starter', 'Starter'),
        ('Beverage', 'Beverage'),
        ('Main Course', 'Main Course'),
        ('Dessert', 'Dessert'),
    )

    name = models.CharField(max_length=150)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
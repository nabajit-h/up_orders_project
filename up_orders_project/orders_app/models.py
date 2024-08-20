from django.db import models
from django.contrib.auth.models import User

# Models
# Custom User Model
class CustomUser(models.Model):
    ROLES = [
        ("Merchant", "Merchant"),
        ("Customer", "Customer"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLES)

    # def __str__(self):
    #     return self.first_name + ' ' + self.last_name
    
# Store
class Store(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    address = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip = models.CharField(max_length=10)
    merchant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ', ' + self.address + ', ' + self.city
    
# Item
class Item(models.Model):
    class Meta:
        unique_together = ('name', 'store')

    CATEGORIES = [
        ("Starter", "Starter"),
        ("Beverage", "Beverage"),
        ("Cold Beverage", "Cold Beverage"),
        ("Snack", "Snack"),
        ("Main Course", "Main Course"),
        ("Dessert", "Dessert"),
        ("Side", "Side")
    ]
    name = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=150, choices=CATEGORIES)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    merchant = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return self.category + ': ' + self.name
    
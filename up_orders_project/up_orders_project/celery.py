from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'up_orders_project.settings')

app = Celery('up_orders_project')

# Configure celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django apps configs
app.autodiscover_tasks()
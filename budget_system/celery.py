from __future__ import annotations
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_system.settings")

app = Celery("budget_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

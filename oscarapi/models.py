from django.db import models


class ApiKey(models.Model):
    key = models.CharField(max_length=255, unique=True)


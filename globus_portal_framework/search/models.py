from django.db import models
from django.contrib.auth.models import User


class Minid(models.Model):
    # ID is a minid
    id = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

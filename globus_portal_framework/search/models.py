from django.db import models
from django.contrib.auth.models import User

MINID_BDBAG = 'BDBAG'

MINID_CATEGORY_CHOICES = (
    (MINID_BDBAG, 'BDBag'),
)

class Minid(models.Model):
    # ID is a minid
    id = models.CharField(max_length=128, primary_key=True)
    users = models.ManyToManyField(User, blank=True)
    category = models.CharField(max_length=128, choices=MINID_CATEGORY_CHOICES)
    description = models.CharField(max_length=128, null=True)
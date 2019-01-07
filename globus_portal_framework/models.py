from django.db import models
from django.urls import reverse


class SearchIndex(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128, blank=True)

    def get_absolute_url(self):
        return reverse('search', index=[str(self.id)])

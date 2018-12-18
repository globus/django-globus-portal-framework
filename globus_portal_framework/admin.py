from django.contrib import admin
from django import forms
from globus_portal_framework import models

import logging

log = logging.getLogger(__name__)


class ConfidentialClientForm(forms.ModelForm):

    client = forms.ChoiceField(choices=models.SearchAuthProxy.get_clients())

    class Meta:
        model = models.SearchAuthProxy
        fields = ('client', 'group')


@admin.register(models.SearchAuthProxy)
class SearchAuthProxyAdmin(admin.ModelAdmin):
    form = ConfidentialClientForm

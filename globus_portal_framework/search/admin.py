from django.contrib import admin

from globus_portal_framework.search.models import Minid


@admin.register(Minid)
class MinidAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')

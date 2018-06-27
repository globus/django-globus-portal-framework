from django.contrib import admin

from globus_portal_framework.search.models import Minid


@admin.register(Minid)
class MinidAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'get_users')

    def get_users(self, minid):
        return ','.join([u.username for u in minid.users.all()])
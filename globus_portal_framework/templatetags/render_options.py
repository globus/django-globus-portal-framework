from django import template

from globus_portal_framework import gpreview

register = template.Library()

@register.simple_tag
def render_options(**kwargs):
    return gpreview.get_render_options(**kwargs)

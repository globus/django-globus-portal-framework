"""
A template helper that allows another template to be rendered as an iframe srcdoc attribute,
  such as for the file preview feature. srcdocs must escape quotes to avoid terminating input early.

  Example usage: {% srcdoc %}{%include tpl %}{% endsrcdoc %}

Based on
  https://github.com/sheepman4267/django-srcdoc/blob/main/src/django_srcdoc/templatetags/srcdoc.py
"""

from django import template

register = template.Library()

class SrcdocNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        content = self.nodelist.render(context)
        result = content.replace('"', '&quot;')
        return result

@register.tag(name="srcdoc")
def do_srcdoc(parser, token):
    nodelist = parser.parse(("endsrcdoc",))
    parser.delete_first_token()
    return SrcdocNode(nodelist)



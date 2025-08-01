"""
Selectively loads template overrides for a particular index. This is useful
if you want to re-use base templates across multiple indices. You must override
``template_override_dir`` in your index, then you can use ``{% index_template %}`` in
your html templates.

For example, an indexes defined as:

.. code-block::

    SEARCH_INDEXES = {
        'my_cool_index': {
                'template_override_dir': 'my_index'
        }
        'my_other_index': {
                'template_override_dir': 'my_other_index'
        }
    }

The app template dir can look like

.. code-block::

    templates/
        my_cool_index/
            globus-portal-framework/
                v3/
                    components/
                        detail-nav.html
                        search-results.html
        my_other_index/
            globus-portal-framework/
                v3/
                    components/
                        search-results.html
                    search.html

In the example above, my_cool_index overrides search-results, so that template
will be included in search.html instead of the default.

In my_other_index, 'detail-nav.html' is not included, so the default will
be used instead.

Both examples here override 'search-results.html' to display custom results.

You specify index templates in the base template using the following:

.. code-block::

    # This specific file goes into your portal and overrides the existing DGPF template:
    # "templates/globus-portal-framework/v3/search-base.html"
    {% extends 'globus-portal-framework/v3/search-base.html' %}
    {% load index_template %}

    ... Lots of HTML code here ...

    {% index_template 'globus-portal-framework/v3/components/search-results.html' as it_search_results %}
    {% include it_search_results %}

In the example above, ``search-base.html`` will attempt to load ``<index_name>/globus-portal-framework/v3/components/search-results.html``
and will fall back on ``globus-portal-framework/v3/components/search-results.html`` if an index-specific template does
not exist.
"""
import re
import logging
from django import template
from globus_portal_framework import get_template

log = logging.getLogger(__name__)

register = template.Library()


class IndexTemplateNode(template.Node):

    def __init__(self, template_name, var_name):
        self.template_name = template_name
        self.var_name = var_name

    def render(self, context):
        template = self.template_name
        try:
            index = context.get('globus_portal_framework', {}).get('index',
                                                                   None)
            if index is not None:
                template = get_template(index, self.template_name)
                if template != self.template_name:
                    log.debug('Loaded custom index template {} for {}'.format(
                              template, index))
        except Exception as e:
            log.exception(e)
        context[self.var_name] = template
        return ''


@register.tag
def index_template(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires arguments" % token.contents.split()[0]
        )
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError('%r tag had invalid arguments' %
                                           tag_name)
    template_name, var_name = m.groups()
    if not (template_name[0] == template_name[-1] and
            template_name[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )
    return IndexTemplateNode(template_name[1:-1], var_name)

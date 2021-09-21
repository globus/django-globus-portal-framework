Facet Modifiers
===============

Modify facet data before it is passed to templates for rendering. This is handy if you re-use the same views for many indices, and want to keep them the same. Configure facet modifiers by setting the `facet_modifiers` on your search index configuration ([See Example](https://github.com/globusonline/django-globus-portal-framework/wiki/Configuring-Facets)). Globus Portal Framework comes with a few built-in facet modifiers:

.. code-block::

  'facet_modifiers': [
      'globus_portal_framework.modifiers.facets.drop_empty',
      'globus_portal_framework.modifiers.facets.sort_terms',
      'globus_portal_framework.modifiers.facets.sort_terms_numerically',
      'globus_portal_framework.modifiers.facets.reverse',
  ],


Each of these modifiers will be applied to facets in the order they are defined. 

### Custom Facet Modifiers

You can add your own modifiers to the list:

.. code-block::

  'facet_modifiers': [
      'globus_portal_framework.modifiers.facets.drop_empty',
      'myapp.modifiers.drop_small_buckets',
      'myapp.modifiers.do_the_thing',
  ],


Each entry in the list is an import string to a Python callable. Each callable needs to take a single argument for the list of facets, and return the new modified list of facets. Modifying the `facets` parameter won't cause issues.

Define the function below in a module that matches the import string above. The function below should be defined in a module called `myapp/modifiers.py`

.. code-block::

  def drop_small_buckets(facets):
      """Drop any buckets on facets with small values. This prevents
      users from gaining insights about search data with carefully crafted
      filtering."""
      for facet in facets:
          if not facet.get('buckets'):
              continue
          facet['buckets'] = [b for b in facet['buckets'] if b['count'] > 5]
      return facets

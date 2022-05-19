Templates
---------

Templates in Globus Portal Framework are an extension of the `Django Template
system <https://docs.djangoproject.com/en/4.0/topics/templates/>`_, consisting 
of a basic set of included templates to make starting a portal quick and easy. 
A list of all `Globus Portal Framework templates <https://github.com/globus/django-globus-portal-framework/tree/main/globus_portal_framework/templates>`_
can be found under the Github template repo.

Your settings.py file should already have been configured during the tutorial,
and should look something like this: 

.. code-block:: python

    # settings.py
    TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [BASE_DIR / 'myproject' / 'templates',],
          'APP_DIRS': True,
          'OPTIONS': {
              'context_processors': [
                  ...
                  'globus_portal_framework.context_processors.globals',
                  'social_django.context_processors.backends',
                  'social_django.context_processors.login_redirect',
              ],
          },
      },
    ]

Templates follow a strict directory layout, file paths must match exactly for
templates to be rendered correctly. Ensure ``myproject`` above matches your
project name, and your ``templates`` directory is created in the correct location.
Globus Portal Framework templates match the following directory structure: 

.. code-block::

  myproject/
      manage.py
      myproject/
          templates/
            globus-portal-framework/
              v2/
                components/
                    detail-nav.html
                    search-facets.html
                    search-results.html
                search.html
                detail-overview.html
                detail-transfer.html

Customizing Search Results
==========================

Let's override the search-results.html template to show a list of fields available
under each search result. 

.. code-block:: python

  # myportal/templates/globus-portal-framework/v2/components/search-results.html
  <h2>Search Results</h2>
  {% for result in search.search_results %}
    <h5>{{result.subject}}</h5>
    <ul>
      {% for field in result.keys %}
      <li>{{field}}</li>
      {% endfor %}
    </ul>
  {% endfor %}

In most cases, your development server should automatically reload the changes
when you navigate to the search page for your project. The template above will be
used to render your search results.


Advanced: Multiple Indices
==========================

If you have multiple search indices and want to re-use the same search views with
different templates, you can set the ``template_override_dir`` for a given index.

.. code-block:: python

  SEARCH_INDEXES = {
      'myindex': {
          ...
          'template_override_dir': 'myproject',
      }
  }

You need to create a directory for the ``template_override_dir`` name you choose,
and place all of your templates within that directory. Your structure should look
like this:

.. code-block::

  myproject/
      manage.py
      myproject/
          templates/
            myproject/  # <-- Create this folder, move all index-specific templates under it
              globus-portal-framework/
                v2/
                  components/
                      detail-nav.html
                      search-facets.html
                      search-results.html
                  search.html
                  detail-overview.html
                  detail-transfer.html

For any views where multi-index templates are supported, Globus Portal Framework will first
attempt to find the index specific template, then will back-off to the 'standard' template
without your project prefix. For example, if you define two templates called
"myportal/templates/globus-portal-framework/v2/components/search-results.html" and
"myportal/templates/myportal/globus-portal-framework/v2/components/search-results.html", when your user visits
the "myportal" index Globus Portal Framework will first try to load
"myportal/templates/myportal/globus-portal-framework/v2/components/search-results.html", then fall back to the
other template if it does not exist.

You can extend this behavior yourself with the "index_template" templatetag.

.. code-block::

  {# Include at the top of the page #}
  {% load index_template %}

  {# Use this to check for a 'template override' for this search index #}
  {% index_template 'globus-portal-framework/v2/components/search-results.html' as it_search_results %}
  {% include it_search_results %}

You can always view the `DGPF template source <https://github.com/globus/django-globus-portal-framework/blob/main/globus_portal_framework/templates/globus-portal-framework/v2/search.html>`_
for a reference.

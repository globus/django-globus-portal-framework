Templates
---------

Templates in Globus Portal Framework are an extension of the `Django Template
system <https://docs.djangoproject.com/en/4.0/topics/templates/>`_, consisting 
of a basic set of included templates to make starting a portal quick and easy. 
A list of all `Globus Portal Framework templates <https://github.com/globus/django-globus-portal-framework/tree/main/globus_portal_framework/templates>`_
can be found under the Github template repo.

Templates follow a strict directory layout, file paths must match exactly for
templates to be rendered correctly. Ensure ``myproject`` above matches your
project name, and your ``templates`` directory is created in the correct location.
Globus Portal Framework templates match the following directory structure: 

.. code-block::

  myportal/
      manage.py
      myportal/
          templates/
            globus-portal-framework/
              v2/
                detail-overview.html
                components/
                    search-results.html

If you want to browse the original templates, you can find them by browsing the
`source template directory <https://github.com/globus/django-globus-portal-framework/tree/main/globus_portal_framework/templates/globus-portal-framework/v2>`_
on github.

Customizing Search Results
==========================

Override `search-results.html` by creating the following file. Make sure the template
directory matches exactly.

.. code-block:: html

  {# myportal/templates/globus-portal-framework/v2/components/search-results.html #}
  <div>
    {% for result in search.search_results %}
    <div class="card my-3">
      <div class="card-header">
        <h3 class="search-title">
          <a href="{% url 'detail' globus_portal_framework.index result.subject %}">{{result.title|default:'Result'}}</a>
        </h3>
      </div>
      <div class="card-body">
        <table class="table table-sm borderless">
          <tbody>
          <tr>
            {% for item in result.search_highlights %}
            <th>{{item.title}}</th>
            {% endfor %}
          </tr>
          <tr>
            {% for item in result.search_highlights %}
            {% if item.type == date %}
            <th>{{item.value | date}}</th>
            {% else %}
            <th>{{item.value}}</th>
            {% endif %}
            {% endfor %}
          </tr>
          </tbody>
        </table>
      </div>
    </div>
    {% endfor %}
  </div>

Reloading the page should result in empty search results. Don't worry, we will fix those in a
minute!

.. note::

  If your new templates don't show up, double check your ``TEMPLATES`` setting. You
  can add a template directly with ``'DIRS': [BASE_DIR / 'myportal' / 'templates']``.


Let's review some template context above:

* ``myportal/templates/globus-portal-framework/v2/components/search-results.html`` -- is the path
  you need to override the base template. This tells Django to replace the existing template
  with the new `search-results.html` file
* ``search.search_results`` -- is context provided by the search view. It contains information on
  the response from the Globus Search query
* ``{% url 'detail' globus_portal_framework.index result.subject %}`` -- builds the detail page
  for viewing specific information about a search result
* ``result (temp var)`` -- contains both raw search information, in addition to any fields defined
  in ``SEARCH_RESULTS.myindex.fields``.
* ``result.search_highlights`` -- is a field that doesn't exist yet, let's create it!

Now to fix search results to make them show up properly. The new field ``search_highlights`` is needed
to pick relavent information to show on the search page. Add the following to your ``fields.py`` file:

.. code-block:: python

  def search_highlights(result):
      """Prepare the most useful pieces of information for users on the search results page."""
      highlight_names = ["author", "date", "tags"]
      search_highlights = list()
      for name, value in result[0].items():
          # Skip value if it's not in the list
          if name not in highlight_names:
              continue

          # Parse the value if needed
          if name == "date":
              highlight_value, highlight_type = datetime.isoparse(highlight_value), "date"
          else:
              highlight_value, highlight_type = value, "str"

          # Add the value to the list
          search_highlights.append(
              {
                  "name": name,
                  "title": name.capitalize(),
                  "value": value,
                  "type": highlight_type,
              }
          )
      return search_highlights

Remember to enable your field in ``settings.py``


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

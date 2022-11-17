Templates
=========

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
^^^^^^^^^^^^^^^^^^^^^^^^^^

Override `search-results.html` by creating the following file. Make sure the template
directory matches exactly.

.. note::

  If no changes to the search page take effect, double check your ``TEMPLATES`` setting in
  your ``settings.py`` file. Ensure a template path is set, or add one with
  ``'DIRS': [BASE_DIR / 'myportal' / 'templates']``.

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
            {% if item.type == "date" %}
            <th>{{item.value | date:"DATETIME_FORMAT"}}</th>
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

  import datetime
  from typing import List, Mapping, Any

  def search_highlights(result: List[Mapping[str, Any]]) -> List[Mapping[str, dict]]:
      """Prepare the most useful pieces of information for users on the search results page."""
      search_highlights = list()
      for name in ["author", "date", "tags"]:
          value = result[0].get(name)
          value_type = "str"

          # Parse a date if it's a date. All dates expected isoformat
          if name == "date":
              value = datetime.datetime.fromisoformat(value)
              value_type = "date"
          elif name == "tags":
              value = ", ".join(value)

          # Add the value to the list
          search_highlights.append(
              {
                  "name": name,
                  "title": name.capitalize(),
                  "value": value,
                  "type": value_type,
              }
          )
      return search_highlights


And add the new setting in ``settings.py``

.. code-block:: python

    "fields": [
          ...
          ("search_highlights", fields.search_highlights),
      ],

Search results will now look much nicer!


Customizing the Detail Page
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Modifying the result detail page will be similar to adding search highlights above with some
differences. The approach begins the same way, by creating a file that shadows the name of
the original.

.. code-block:: html

  {% extends 'globus-portal-framework/v2/detail-overview.html' %}

  {% block detail_search_content %}

  <h3 class="text-center mb-5">General Info</h3>
  <div class="row">
    <div class="col-md-6">
      {% include 'globus-portal-framework/v2/components/detail-dc-metadata.html' %}
    </div>
    <div class="col-md-6">
      {% include 'globus-portal-framework/v2/components/detail-general-metadata.html' %}
    </div>
  </div>

  {% endblock %}


Make sure the filename is ``myportal/templates/globus-portal-framework/v2/components/search-results.html``
Let's review some differences in this template:

* ``extends`` - This template builds on the existing template instead of replacing it
* ``block`` - Tells Django to replace this specific content with our own
* ``include`` - Include some additional templates to render some specific data

   * `DC Metadata <https://github.com/globus/django-globus-portal-framework/blob/main/globus_portal_framework/templates/globus-portal-framework/v2/components/detail-dc-metadata.html>`_ - A template to render metadata in Datacite Format
   * `General Metadata <https://github.com/globus/django-globus-portal-framework/blob/main/globus_portal_framework/templates/globus-portal-framework/v2/components/detail-general-metadata.html>`_ - A template to render any project-specific metadata

The dc and general project metadata templates help render commonly desired fields for the detail
page. Their use is entierly optional. They require fields named `dc` and `project_metadata` respectively,
see the following new fields below.

.. code-block:: python

  def dc(result):
      """Render metadata in datacite format, Must confrom to the datacite spec"""
      date = datetime.datetime.fromisoformat(result[0]['date'])
      return {
          "formats": ["text/plain"],
          "creators": [{"creatorName": result[0]['author']}],
          "contributors": [{"contributorName": result[0]['author']}],
          "subjects": [{"subject": s for s in result[0]['tags']}],
          "publicationYear": date.year,
          "publisher": "Organization",
          "dates": [{"date": date,
                    "dateType": "Created"}],
          "titles": [{"title": result[0]['title']}],
          "version": "1",
          "resourceType": {
              "resourceTypeGeneral": "Dataset",
              "resourceType": "Dataset"
          }
      }


  def project_metadata(result):
      """Render any project-specific metadata for this project. Does not conform to
      a spec and can be of any type, although values should be generally human readable."""
      project_metadata_names = ['times_accessed', 'original_collection_name']
      return {k: v for k, v in result[0].items() if k in project_metadata_names}

Add the fields to settings.py.


.. code-block:: python

    "fields": [
          ...
          ("dc", fields.dc),
          ("project_metadata", fields.dc),
      ],

  And the detail page will now be much nicer.

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

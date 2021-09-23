Customizing Fields and Templates
--------------------------------

Fields and templates go hand in hand. Fields are top-level entries within
individual search records, used within your portal, that are provided as context
within Django Templates in order to be rendered to the user. In addition to
selecting metadata in search records, fields can include a function to provide
custom formatting or fetch additional data. Here is an example:

.. code-block:: python

  # settings.py
  import datetime

  def format_my_dates(search_result):
      # My dates are all UTC timestamps, Ex. 1552508657
      return datetime.datetime.frometimestamp(search_result[0]['my_date'])

  SEARCH_INDEXES = {
      'myindex': {
          'name': 'My Cool Index',
          'uuid': 'f707d9b0-1462-4ab5-a7c2-064fac0e8006',
          'fields': [
              # Fetches 'my_general_metadata' from your search record
              'my_general_metadata',
              # Calls a function with your search record as a parameter
              ('formatted_dates', format_my_dates),
          ],
          'template_override_dir': 'myindex',
      }
  }

The two fields, `my_general_metadata` and `formatted_dates` can then be used in templates.
A small example is below. `myproject/myproject/perfdata/components/search-results.html`

.. code-block:: python

  <h2>Search Results</h2>
  {% for result in search.search_results %}
    <h5>{{result.my_general_metadata.title}}</h5>
    {{result.date|date}}
  {% endfor %}


Configuring Your Portal
=======================

"perfdata" is an active Globus Search index in the example below. You will
need to add some configuration to your `settings.py` file in order for
templates to work. You will also need to ensure you place your template HTML in
the correct directory for Django to pick it up and render it.

In `settings.py`

.. code-block:: python

  SEARCH_INDEXES = {
      'perfdata': {
          'name': 'Performance Data',
          'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
          'fields': [
              # List any data you want to use in your search results
              'perfdata',
              ('title', lambda result: result[0]['perfdata']['titles'][0]['value']),
          ],
          'template_override_dir': 'perfdata',
      }
  }

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

`TEMPLATES` specifies the Django folder where your templates are stored. For each index,
you can also define `template_override_dir` for overriding templates for `only that index`. It's
possible to have the following layout:

.. code-block::

  myproject/
      manage.py
      myproject/
          templates/
              perfdata/
                  components/
                      detail-nav.html
                      search-facets.html
                      search-results.html
                  search.html
                  detail-overview.html
              detail-transfer.html


Create a template to override how search results are displayed. You must name it exactly the same as the template you want to override.

`myproject/myproject/perfdata/components/search-results.html`

.. code-block:: html

  <h2>Search Results</h2>
  <div id="search-result" class="search-result">
    {% for result in search.search_results %}
    <div class="result-item">

      <h3 class="search-title mt-3">
        <a href="{% url 'detail' globus_portal_framework.index result.subject %}">{{result.title}}</a>
      </h3>
      <div class="result-fields">
        Description: {% for desc in result.perfdata.descriptions %}
                        {{desc.value}}
                        {% endfor %}
        <br>
        {% if result.perfdata.filesystem %}
        Filesystem: {{result.perfdata.filesystem.value}}
        <br>
        {% endif %}
        {% if result.perfdata.maximum_file_size %}
        Maximum File Size: {{result.perfdata.maximum_file_size.value}}
        <br>
        {% endif %}
        {% if result.perfdata.organization %}
        Organization: {{result.perfdata.organization.value}}
        <br>
        {% endif %}
        Date: {{result.perfdata.publication_year.value}}
        <br>
        Contributors: {% for contributor in result.perfdata.contributors %}
        {{contributor.contributor_name}}{% if not forloop.last %};{% endif %}
        {% endfor %}
        <br>
        Formats:
        {% for format in result.perfdata.formats %}
        <button class="btn btn-primary btn-sm ml-1 py-0" style="background-color: #337ab7">
          {{format.value}}
        </button>
        {% endfor %}
        <br>
      </div>

    </div>
    {% endfor %}
  </div>

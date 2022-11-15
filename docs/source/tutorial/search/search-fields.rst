Search Fields
-------------




Search Fields allow you to add a tiny snippet of code for processing a specific search field,
so you don't need to modify the whole Django View. Create a view using the following: 

.. code-block:: python

  # fields.py
  import datetime

  def my_date(search_result):
      # My dates are all UTC timestamps, Ex. 1552508657
      return datetime.datetime.fromtimestamp(search_result[0]['my_date'])

  # settings.py
  SEARCH_INDEXES = {
      'myindex': {
          'name': 'My Index',
          'uuid': 'f707d9b0-1462-4ab5-a7c2-064fac0e8006',
          'fields': [
              # Calls a function with your search record as a parameter
              ('my_date', my_date),
          ],
      }
  }

Globus Portal Framework will call your function ``format_my_dates`` any time it does a Globus Search or
views a Globus Search subject. For searches, the function will be called for each search result, and only
once when viewing a subject.

You can use the field above in the following template:

.. code-block::

  {# templates/globus-portal-framework/v2/components/search-results.html #}
  <h2>Search Results</h2>
  {% for result in search.search_results %}
    <h5>{{result.subject}}</h5>
    <ul>
      <li>Date: {{result.my_date|date}}
    </ul>
  {% endfor %}
  
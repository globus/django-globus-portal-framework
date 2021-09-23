Configuring Facets
==================


General Info: 

* `facets.name` -- The title for this category of facet
* `facets.field_name` -- Field in your Globus Search results to facet
* `facets.type` -- Configure the type of faceting to use, depending if the value is a string, number, or date. Default 'terms' if blank. 
  * `terms` -- Used for faceting on keywords, such as 'apple', 'banana', 'fruit'.
  * `numeric_histogram` -- Used for generating ranges between numerical values. 
  * `date_histogram` -- Facet on date intervals, such as 'years', 'months', 'days', 'hours', 'minutes', 'seconds'
* `facets.size` -- configure behavior of returned facets
    * `terms` -- limits the number of buckets returned by Globus Search
    * `histogram` -- number of intervals to create between 'low' and 'high'
* `facet_modifiers` -- Modify facets before they are rendered in templates. Allows for changing facets per-index without changing views. See [extended docs on facet modifiers here](https://github.com/globusonline/django-globus-portal-framework/wiki/Facet-Modifiers).
* `filter_match` -- Configure default match filtering for all 'terms' facets in this index. Overrides `settings.DEFAULT_FILTER_MATCH`, but can be overridden by setting `filter_match` on a facet definition. 
  * `match-all` -- Filter only on exact matches, exclude all other results
  * `match-any` -- Include all facets, filter and return results for any results that match

Information in facets is checked and forwarded on to Globus Search. See the documentation below for extended information about how to configure facets:

[Globus Search Documentation](https://docs.globus.org/api/search/search/#request_documents) 

Example
^^^^^^^

The following is an example SEARCH_INDEXES inside ``myproject/settings.py``

.. code-block::
    
    SEARCH_INDEXES = {
        'perfdata': {
            'name': 'Performance Data Portal',
            'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
            'fields': [],
            'facets': [
                {
                    'field_name': 'perfdata.subjects.value',
                },
                {
                    'name': 'Subjects',  # Display Name
                    'field_name': 'perfdata.publication_year.value',
                    'type': 'terms',  # Category of facet. Default "terms".
                    'size': 10  # Number of Facets, default 10.
                },
                {
                    'name': 'File Size (Bytes)',
                    'type': 'numeric_histogram',
                    'field_name': 'remote_file_manifest.length',
                    'size': 10,
                    'histogram_range': {'low': 15000, 'high': 30000},
                },
                {
                    'name": 'Dates',
                    'field_name": 'perfdata.dates.value',
                    'type': 'date_histogram',
                    'date_interval": 'month',
                },
            ],
            'facet_modifiers': [
                'globus_portal_framework.modifiers.facets.drop_empty',
            ],
            'filter_match': 'match-all',
        }
    }

.. _search_settings_reference:

Search Settings Reference
=========================

This reference contains all search related settings that go in ``settings.py``


Search Indices
--------------

Configure your Globus Search indexes with the ``SEARCH_INDEXES`` variable in your 
`myproject/settings.py` file. Below are all of the main top-level fields. The following
match directly with Globus Search fields, and match directly with Globus Search.

* facets
* sort
* boosts
* bypass_visible_to
* result_format_version

See more information in the `Globus Search documentation <https://docs.globus.org/api/search/reference/post_query/#gsearchrequest>`_

=====================  ===========
Field Name             Description     
=====================  ===========
name                   The title of this search index. 
uuid                   The Globus Search UUID for this Globus Search Index
fields                 User defined functions for processing metadata returned by Globus Searches
facets                 Display stats on search results, provide corresponding filters for future Searches
facet_modifiers        Change how facets are displayed. See :ref:`facet_modifiers`
sort                   Sort results of a Globus Search
boosts                 Increase or decrease values of fields
filter_match           Default filtering on 'term' facets. 'match-any' or 'match-all' supported
template_override_dir  Directory for using different custom templates per-index on a multi-index portal
result_format_version  Version of Search Result documents to return
bypass_visible_to      Show all search records regardless visible_to permission (index admins only)
=====================  ===========


Search Settings Example
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: 

    SEARCH_INDEXES = {
        'myportal': {
            'name': 'My Science Portal',
            'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
            'fields': [
                'my_title'
            ],
            'facets': [
                {
                    'field_name': 'foo.bar.baz',
                }
            ],
            'sort': [
                {
                    'field_name': 'path.to.date',
                    'order': 'asc'
                }
            ]
            'boosts': [
                {
                    'field_name': 'author',
                    'factor': 5
                }
            ],
            'filter_match': 'match-all',
            'template_override_dir': 'myportal',
            'bypass_visible_to': True,
        }
    }


Configuring Facets
------------------

Field information for each list entry defined in "facets" is described here. Information within each object is
checked and mostly forwarded on to Globus Search. See more information in the `Globus Search documentation <https://docs.globus.org/api/search/reference/post_query/#gsearchrequest>`_

=====================  =======  ===========
Field Name             Type     Description     
=====================  =======  ===========
name                   String   Title for this facet 
field_name             String   The search metadata field where this facet should be applied
type                   String   Type of facet. Supported: terms, date_histogram, numeric_histogram, sum, avg
size                   Integer  Number of 'buckets' to return
histogram_range        Object   Contains 'low' and 'high' number or date to specify range bounds
date_interval          String   Date Unit to use. Supported: years, months, days, hours, minutes, seconds
=====================  =======  ===========

For more information on how facets can be displayed, See :ref:`facet_modifiers`

Facet Setting Example
^^^^^^^^^^^^^^^^^^^^^

The following is an example SEARCH_INDEXES inside ``myproject/settings.py``

.. code-block::
    
    SEARCH_INDEXES = {
        'myportal': {
            'name': 'My Portal',
            'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
            'fields': [],
            'facets': [
                {
                    'name': 'Term Facets',
                    'field_name': 'mybooks.genre',
                },
                {
                    'name': 'Dates',
                    'field_name': 'dc.dates.date',
                    'type': 'date_histogram',
                    'date_interval': 'day',
                },
                {
                    'name': 'File Sizes',
                    'field_name': 'files.length',
                    'type': 'numeric_histogram',
                    'histogram_range': {'low': 0, 'high': 10000}
                },
            ],
            'facet_modifiers': [
                'globus_portal_framework.modifiers.facets.drop_empty',
            ],
            'filter_match': 'match-all',
        }
    }

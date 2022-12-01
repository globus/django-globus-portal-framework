Configuring Facets
==================

Facets are used to filter and query your search index. To configure them, add a new field 
called ``facets`` to ``SEARCH_INDEXES``. A basic example is below:

.. code-block:: python

  SEARCH_INDEXES = {
      'index-slug': {
          'name': 'My Search Index',
          'uuid': 'my-search-index-uuid',
          'facets': [
            {
              'name': 'Tags',
              'field_name': 'tags'
            },
          ],
      }
  }


Now, the next time the portal is ran, the new ``Tags`` facet will show up for any
search records matched in the query. Given a record with content that looks like the following:

.. code-block:: json

    {
      "title": "File Number 1",
      "url": "globus://ddb59af0-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt",
      "author": "Data Researcher",
      "tags": ["globus", "tutorial", "file"],
      "date": "2022-11-15T12:31:28.560098"
    }

The default search page should show the ``Tags`` facet on the left side with each value,
``globus``, ``tutorial``, and ``file``. Each additional search record will add to this
list, and repeating numbers will increment the number for each value.

.. note::
    Only results with matching fields (``tags`` above) will show up in the results. By default,
    facets which match no record are not shown. 

New sets of ``{'name': ..., 'field_name': ...},`` can be added to the list of ``facets`` in order
to provide more filtering options. In all cases, while ``name`` can be any string value, ``field_name`` 
must be a component found in the ``content`` section of at least one of the ingested search records.

See :ref:`search_settings_reference` for more information on different facet types and options.

Filters
^^^^^^^

By default, Django Globus Portal Framework shows facets on the left side of the search page with
check marks. Checking any item on the left will cause the portal to filter on the information given.

Filtering at this time is automatically handled by the portal for all facet types. 
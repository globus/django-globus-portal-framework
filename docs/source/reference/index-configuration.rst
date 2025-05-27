.. _index_configuration:

Index Configuration
===================

Configure your Globus Search index in your settings.py file with the keyword ``SEARCH_INDEXES``:

.. code-block:: python

  SEARCH_INDEXES = {
      'my-index-slug': {
          'name': 'My Search Index',
          'uuid': 'my-index-uuid',
      }
  }

You *must* name your search index slug `my-index-slug`. The slug is used to determine
the URL for your search index (default: ``https://mysite/my-index-slug/``). The `uuid` must
also be set to tell the portal which search index to search.

See :ref:`index_creation` for more information.

Index Search Settings
---------------------

Most settings for each setting in SEARCH_INDEXES modify the *search* behavior when a
user navigates to the search URL page, and many values here are simply passed through
directly to Globus Search whenever a user queries an index.

Three exceptions to this are ``q``, ``limit``, and ``offset``, which are determined
by the search page instead of via configuration here.

Some options below are only available with a particular Globus Search ``@version``.

See the `Globus Search Documentation <https://docs.globus.org/api/search/reference/post_query/#gsearchrequest>`_
for more information on select fields.

===================== ==================
Name                  Type       
===================== ==================
@version              String
advanced              Boolean
q_settings            Dict
bypass_visible_to     Boolean
filter_principal_sets List of Strings
filters               Array
facets                Array
post_facet_filters    Array
boosts                Array
sort                  Array
===================== ==================

Index Portal Settings
---------------------

Some additional index settings drive portal behavior instead of search
behavior. 

.. note::
    Developers may add their own fields here to take advantage of per-index
    configuration. Additional custom fields are ignored by the portal. However,
    Globus Portal Framework may add additional fields here which conflict
    with your portal.

===================== ====== ===========
Name                  Type   Description    
===================== ====== ===========
uuid                  String The configured Globus Search index uuid to perform searches
name                  String The human readable name the portal should use for this index
===================== ====== ===========

Referencing Indices in Views
----------------------------

You can reference these settings in your view with the following:

.. code-block:: python

    from globus_portal_framework.gsearch import get_index
    index_data = get_index("my-index-slug")
    print(f"My index {index_data['name']} has uuid {index_data['uuid']}")
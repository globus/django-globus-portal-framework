Search Setup
============

.. warning::
  These docs are still preliminary and missing some finer detail on search ingest.
  We will add a more comprehensive update in the future.


Before you can configure your Globus Search index, you will need to create your
own and ingest data into it. A few different resources exist for creating indices
and ingesting metadata, a few of them are here:

* `The Metadata Search and Discovery <https://jupyter.demo.globus.org>`_
* `Globus Pilot <https://github.com/globus/globus-pilot/blob/main/docs/source/user-guide.rst>`_

For most Globus Portal Framework projects, we use Globus Pilot to manage data on a Globus
Endpoint with data in Globus Search. Use these steps to get started:

.. code-block:: bash

  pip install globus-search-cli globus-pilot
  globus-search login
  globus-search index create myindex
  pilot login
  pilot index set <myindex-uuid>
  pilot index setup

When settig up your Search index in the Globus Search portal, you should have an
index UUID and one or two documents inside your search index.

Use SEARCH_INDEXES in your settings.py file to define your search indexes:

.. code-block:: python

  SEARCH_INDEXES = {
      'perfdata': {
          'name': 'Performance Data Portal',
          'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
          'fields': [],
          'facets': [],
          'sort': [],
          'boost': [],
          'filter_match': 'match-all',
          'template_override_dir': 'perfdata',
          'bypass_visible_to': True,
      }
  }

Many of the settings above correspond to `Globus Search settings <https://docs.globus.org/api/search/reference/post_query/>`_.

Authenticated Search
^^^^^^^^^^^^^^^^^^^^

If your search records are private, you will need to login to view them. Make sure you
have Globus Auth setup, and you have a search scope set in your settings.py file.

.. code-block::

  SOCIAL_AUTH_GLOBUS_SCOPE = [
      ...
      'urn:globus:auth:scope:search.api.globus.org:search',
  ]

After login, User tokens will automatically be sent with each search query.

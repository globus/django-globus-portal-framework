Creating your Search Index
==========================

The `Globus Search <https://docs.globus.org/api/search/>`_ Index stores the metadata 
for your search potral. Globus Portal Framework queries and presents this information
in a way that's convenient for users.

Creating the Index
^^^^^^^^^^^^^^^^^^

Creating and ingesting to your index are both tasks that happen independent of running
a portal. There are a few different tutorials on creating a search index and ingesting
data into it. If you would like an interactive guide and learn more, there are
a few different tutorials to choose from:


* `Metadata Search and Discovery <https://github.com/globus/globus-jupyter-notebooks/blob/master/Metadata_Search_and_Discovery.ipynb>`_
    * Run interactively on `jupyter.demo.globus.org <https://jupyter.demo.globus.org>`_!
* `Gladier Flows Tutorial <https://github.com/globus/globus-jupyter-notebooks/blob/master/Gladier%20Flows%20Tutorial.ipynb>`_
* `Searchable Files Demo <https://github.com/globus/searchable-files-demo>`_

The `Globus CLI <https://docs.globus.org/cli/#installation>`_ can now be used to manage 
index settings. Use the following to get started:

.. code-block:: bash

  pipx install globus-cli
  globus search index create myindex "A description of my index"


Ingesting Metadata
^^^^^^^^^^^^^^^^^^

Metadata within Globus Search is unstructured and can be tailored to the specific needs
of the project. Creating a schema which will apply to all of your search results is optional,
but highly recommended. Below are tools for getting started.

In simple terms, a search result is a JSON document with a "subject" containing user defined
content. An example is below:

.. literalinclude:: ../../examples/simple-ingest-doc.json
   :language: python

And the document can be ingested into your index above with the following: 

.. code-block:: bash

  globus search ingest my-index-uuid simple-ingest-doc.json

Working from inside out, everything under the ``content`` block is completely defined by the
user. Each new ingested field Globus Search detects will be scanned and indexed, and can be
search upon immediately after ingest. ``visible_to`` defines access, and ``subject`` is a
unique identifier for the search result. ``id`` defines different independent sub-categories
under ``subject``. 

.. warning:: 
  Field types in Globus Search may only be set once the first time you ingest a new field. Types
  may not change for the lifetime of the index. Setting new types requires the index to be either
  reset or recreated. Both require emailing support at support@globus.org.

  For example above: "author" and "url" are both string types, and future ingest for those fields
  must also be strings. Non-string values will raise an error if the types change.

That's it for the actual metadata. The outer envelope of the sample above ``ingest_data`` and ``gmeta`` 
define the document as a search ingest document. See the `ingest documentation <https://docs.globus.org/api/search/ingest/#gmetaentry_subjects_and_entries>`_
for more info.


Portal Configuration
^^^^^^^^^^^^^^^^^^^^



``SEARCH_INDEXES`` defines one or more search indices in your settings.py file. Use the ``uuid``
you created with the ``globus search index create`` command above here:

.. code-block:: python

  SEARCH_INDEXES = {
      'index-slug': {
          'name': 'My Search Index',
          'uuid': 'my-search-index-uuid',
          'facets': [
            {
              'name': 'Elements',
              'field_name': 'elements'
            }
          ],
      }
  }

At a minimum, you must set your index ``uuid`` and ``slug`` above. ``name`` and ``facets`` are optional
additions to make your portal look nicer.

Authenticated Search
^^^^^^^^^^^^^^^^^^^^

If search records contain anything other than ``public`` inside ``visible_to``, users
will need to login to view records.  Make sure you
have Globus Auth setup, and you have a search scope set in your settings.py file.

.. code-block::

  SOCIAL_AUTH_GLOBUS_SCOPE = [
      ...
      'urn:globus:auth:scope:search.api.globus.org:search',
  ]

It's common for different Globus Groups to be set on various records on the ``visible_to``
field. Records will simply not show up for users who do not have access.

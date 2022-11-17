.. _index_creation:


Index Creation and Ingest
=========================

The `Globus Search <https://docs.globus.org/api/search/>`_ Index stores the metadata 
for your search potral, and Globus Portal Framework queries and presents this information
in a way that's convenient for users. No search metadata is stored directly on the portal,
rather the portal is only a graphical interface for constructing search queries for users
and presenting the information in a digestable fashion.

Before any work can be done on a portal, the search index must first be created in Globus
Search and metadata ingested into it. Once the search index can be queried for information,
the portal can be configured to display results for users.

Creating the Index
^^^^^^^^^^^^^^^^^^

There are a few different tutorials on creating a search index and ingesting
data into it. If you would a deeper dive beyond the basics, see the resouces
below:

* `Metadata Search and Discovery <https://github.com/globus/globus-jupyter-notebooks/blob/master/Metadata_Search_and_Discovery.ipynb>`_
    * A fast and friendly tutorial on the basics of Globus Search
    * Run interactively on `jupyter.demo.globus.org <https://jupyter.demo.globus.org>`_!
* `Gladier Flows Tutorial <https://github.com/globus/globus-jupyter-notebooks/blob/master/Gladier_Flows_Tutorial.ipynb>`_
    * An automated approach to ingesting metadata into an index
    * Run interactively on `jupyter.demo.globus.org <https://jupyter.demo.globus.org>`_!
* `Searchable Files Demo <https://github.com/globus/searchable-files-demo>`_
    * A deeper dive into maintaing a Globus Search index

The `Globus CLI <https://docs.globus.org/cli/#installation>`_ can now be used to manage 
index settings. Use the following to get started:

.. code-block:: bash

  pipx install globus-cli
  globus search index create myindex "A description of my index"

Should return something that looks like:

.. code-block::

  Index ID:     3e2525cc-e8c1-49cd-bef5-a9566770d74c
  Display Name: myindex
  Status:       open

Take note of the Index ID UUID returned by this command, this will be used later to point your portal
at your new search index.


Ingesting Metadata
^^^^^^^^^^^^^^^^^^

.. note::
  See the reference ingest document for a real-world example. The document below is 
  oversimplified for readablility.

Metadata within Globus Search is unstructured and can be tailored to the specific needs
of the project. In simple terms, a search result is a JSON document with a "subject" 
containing user defined content. See the ``simple-ingest-doc.json`` below:

.. literalinclude:: ../../examples/simple-ingest-doc.json
   :language: json

The document can be ingested into your index above with the following:

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

``SEARCH_INDEXES`` defines one or more search indices in your ``myportal/settings.py`` file. Use the ``uuid``
from the index create command above in :ref:`index_creation`.

.. code-block:: python

  SEARCH_INDEXES = {
      'my-index-slug': {
          'name': 'My Search Index',
          'uuid': 'my-search-index-uuid',
      }
  }

The configuration above consists of three pieces of information:

* ``my-index-slug`` -- The slug for your index. This will map to the url and can be any reasonable value.
* ``name`` -- The name for your index. This shows up in some templates and can be any value.
* ``uuid`` -- The Globus Search index uuid. Can be found with ``globus search index list``

You should now have enough information to run your new portal.

.. code-block:: bash

  python manage.py runserver localhost:8000

The name should show up on the index selection page at ``http://localhost:8000``, and the search record should 
now show up on the ``http://localhost:8000/my-index-slug/``. The existing record can be edited by
re-ingesting the same subject with different content, or new records can be created by changing the subject.

Next, we will add facets to this portal.

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

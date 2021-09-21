Configuring Your Index
======================

Configure your Globus Search indexes with the ``SEARCH_INDEXES`` variable in your 
`myproject/settings.py` file. 


* The key ("perfdata" above) is used to construct the URL for Search Records.
* `name` can be arbitrary, and is used by templates.
* `uuid` is the UUID of the Globus Search index you are using.
    * If you don't know your UUID, DGPF will attempt to look it up using the key above (Ex. "perfdata")
* [`fields`](Customizing-Fields-and-Templates.md) lists the data extracted for every search result
* [`facets`](Configuring-Facets.md) provides an easy way to filter down search results based on categories.
* [`sort`](https://docs.globus.org/api/search/search/#gsort) Sort results for each search
* [`boosts`](https://docs.globus.org/api/search/search/#gboost) Increase or decrease values of fields for each search
* [`filter_match`](https://docs.globus.org/api/search/search/#gfilter) the default filtering behavior for 'term' type facets.
  * `match-all` -- Filter only on exact matches, exclude all other results
  * `match-any` -- Include all facets, filter and return results for any results that match
* [`template_override_dir`](Customizing-Fields-and-Templates.md#configuring-your-portal) The directory for overriding DGPF templates with your own custom ones.
* `bypass_visible_to` -- Show all records, even if not allowed by a records `visible_to` setting. 
  * Note: This option only works for admins on the index. It has no effect for other users.
* Extended Args -- Other args not listed here (bypass_visible_to, advanced, result_format_version) can also be defined in an index, and will be passed on to Globus Search. See the [Globus Search Docs](https://docs.globus.org/api/search/search/) for a complete list.

Example
^^^^^^^

Here is an example below: 

.. code-block:: 

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


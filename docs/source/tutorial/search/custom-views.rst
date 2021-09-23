Custom Search Views
===================

.. note::
  **Note**: Most portals shouldn't need these changes, it's only necessary if you need
  finer control over the low level components that make requests to the Globus Search service.
  Try customizing your search templates [here first](https://github.com/globusonline/django-globus-portal-framework/wiki/Customizing-Fields-and-Templates).

At some point, you may need more control over the context for your search templates.
An example may be rendering graphs based on the statistics returned by facets.
The examples below include writing your own 'search' view, and wiring it up to
override the default search view provided by Globus Portal Framework.
This requires two changes:

* views.py -- Writing a custom view to capture a user search parameters and return context to the portal
* urls.py -- Apply the custom view to one or more of your indices

In your project's urls.py:

.. code-block:: python

  from django.urls import path, include
  from globus_portal_framework.urls import register_custom_index
  from exalearn.views import mysearch

  # Register a new custom index converter.
  register_custom_index('custom_search', ['myindex'])

  urlpatterns = [
      # Override 'search' url with custom search view
      path('<custom_search:index>/', mysearch, name='search'),
      # Provides the basic search portal
      path('', include('globus_portal_framework.urls')),
      path('', include('globus_portal_framework.urls_debugging')),
      path('', include('social_django.urls', namespace='social')),
  ]


The URLs are still very similar to the old ones, except for the `register_custom_index` line.
This registers a new [Django URL Converter](https://docs.djangoproject.com/en/2.2/topics/http/urls/#registering-custom-path-converters) for the indices you include in the second argument. This does a couple things:

* Only the indices you include will use the new functionality
* Unrelated URLs won't match as an 'index', such as if a bot searches for '/robots.txt'. Only URLs which map to the indices you include in the list will be matched.

In your project's views.py:

.. code-block:: python

  from django.shortcuts import render
  from globus_portal_framework.gsearch import post_search, get_search_query, get_search_filters, get_template

  def mysearch(request, index):
      query = get_search_query(request)
      filters = get_search_filters(request)
      context = {'search': post_search(index, query, filters, request.user,
                                       request.GET.get('page', 1))}
      return render(request, get_template(index, 'search.html'), context)


With the above, we're using a number of components to prepare and process the search:

 * `get_search_query` fetches the user's query from the query params on the request
 * `get_search_filters` fetches any filters in query params that should be applied to the search
 * `post_search` prepares and sends the request to Globus Search, in addition to processing the results based on configuration defined in settings.SEARCH_INDEXES
 * `get_template` will attempt to grab an overridden custom index template if it exists (templates/myindex/search.html), grab a standard overridden template (templates/search.html), or simply render the basic Globus Portal Framework search.html template


We Need To Go Deeper
--------------------

It's possible to access the lowest level mechanism to modify requests made to Globus Search. Again, most use-cases shouldn't require this, but it may be necessary if you need to utilize Globus Search feature not provided by Globus Portal Framework. If this is the case, consider opening an issue, so we can provide the feature for others. 

Advanced search views.py

.. code-block:: python

  from django.shortcuts import render
  from globus_portal_framework.gsearch import (
      get_search_query, get_search_filters,
      process_search_data, get_facets, get_template, get_index
  )
  from globus_portal_framework.gclients import load_search_client


  def my_advanced_search(request, index):
      index_data = get_index(index)
      search_cli = load_search_client(request.user)
      query = get_search_query(request)
      filters = get_search_filters(request)
      data = {'q': query,
              'filters': filters}
      result = search_cli.post_search(index_data['uuid'], data)
      search_data = {
          'search_results': process_search_data(index_data.get('fields', []),
                                                result.data['gmeta']),
          'facets': get_facets(result, index_data.get('facets', []),
                               filters, index_data.get('filter_match')),
      }
      context = {'search': search_data}
      return render(request, get_template(index, 'search.html'), context)


The custom search function above allows for extended flexibility in what gets sent to Globus Search and the resulting context you want rendered in your templates. There are a few new components we're using:

* `get_index` Will search settings.SEARCH_INDEXES for your index, and return data associated with it.
* `load_search_client` Will fetch the base globus_sdk.SearchClient class loaded with an authorizer for the current user (Or nothing, if the user is logged out). 
* `process_search_data` applies the `fields` defined in settings.SEARCH_INDEXES to the search data returned by Globus Search. 
* `get_facets` processes the facet data returned by Globus Search, and prepares the context so that users can filter on those facets on their next action. 
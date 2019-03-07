# django-globus-portal-framework

A collection of tools for quickly bootstrapping a portal for use with Globus
Tools, including Globus Search, Transfer, Auth, and more! Drop in pre-built
defaults to get started quickly, and easily tweak any component when you
need to do things your way.

## Requirements

* Python 3
* Django 2.0

## 5 Minute Quick-Start

Let's get started with a simple Globus Search portal.

```
    $ pip install django-admin
    $ pip install -e git+https://github.com/globusonline/django-globus-portal-framework#egg=django-globus-portal-framework
    $ django-admin startproject myproject
    $ cd myproject
```

Integrate it into your app in `myproject/settings.py`

```
    INSTALLED_APPS = [
        ...
        'globus_portal_framework',
    ]
```

Then wire up the search portal in your `myproject/urls.py`

```
    from django.urls import path, include

    urlpatterns = [
        path('', include('globus_portal_framework.urls')),
    ]
```

Lastly, set the context processor in `myproject.settings`. The context processor adds metadata about indexes to the
portal:

```
    TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'globus_portal_framework.context_processors.globals',
            ]
        }
    }
```

Run migrations and startup your project:

```
    $ python manage.py migrate
    $ python manage.py runserver
```

That's it! Your server will be running at `http://localhost:8000`.

## Adding Globus Auth

You probably want to add Globus Auth so users can login to view confidential
search results, transfer files, or do work with custom tokens.

First off, create a [Developer App](https://developers.globus.org). If you're new
to Globus apps or want a reference, [see here](https://docs.globus.org/api/auth/developer-guide/#developing-apps)

For our portal, ensure your Globus App has these settings:

* **Redirect URL**--http://localhost:8000/complete/globus/
* **Native App**--Unchecked

After you create your app, add these to `myproject/settings.py`

```
    SOCIAL_AUTH_GLOBUS_KEY = '<YOUR APP CLIENT ID>'
    SOCIAL_AUTH_GLOBUS_SECRET = '<YOUR APP SECRET>'

    INSTALLED_APPS = [
        ...
        'globus_portal_framework',
        'social_django',
    ]

    MIDDLEWARE = [
        ...
        'social_django.middleware.SocialAuthExceptionMiddleware',
        'globus_portal_framework.middleware.ExpiredTokenMiddleware',
        'globus_portal_framework.middleware.GlobusAuthExceptionMiddleware',

    ]

    AUTHENTICATION_BACKENDS = [
        'globus_portal_framework.auth.GlobusOpenIdConnect',
        'django.contrib.auth.backends.ModelBackend',
    ]

    TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'globus_portal_framework.context_processors.globals',
            ]
        }
    }
```

Add Social Django's Login URLs to your project in `myproject/urls.py`:

```
from django.urls import path, include

urlpatterns = [
    path('', include('globus_portal_framework.urls')),
    path('', include('social_django.urls', namespace='social')),
]
```

Run migrations and startup your project:

```
    $ python manage.py migrate
    $ python manage.py runserver
```

Now you can login at `http://localhost:8000`

## Adding Globus Transfer

Ensure you have the transfer scope set in `myproject/settings.py`

    SOCIAL_AUTH_GLOBUS_SCOPE = [
        'urn:globus:auth:scope:search.api.globus.org:search',
        'urn:globus:auth:scope:transfer.api.globus.org:all',
    ]

You can now transfer these files to any endpoint! Remember you need to re-login
in order for Globus Auth to request the Transfer Scope.

See _Configure Fields_ below for setting which files are transferred for the search
results you define.


## Adding Globus Preview

You will need to setup a Globus HTTP endpoint on top of your GCS endpoint,
which is not covered by this tutorial. Given that you have an HTTP endpoint setup, you
can add it with the following settings:


    SOCIAL_AUTH_GLOBUS_SCOPE = [
        ...
        'urn:globus:auth:scope:search.api.globus.org:search',
        'https://auth.globus.org/scopes/56ceac29-e98a-440a-a594-b41e7a084b62/all'
    ]



See _Configure Fields_ below for setting the endpoint, resource server, and path
for preview.

## Customizing Your Portal

Now for the fun stuff, customizing the portal to your specific use case.

### Configure Search Indexes

Use `SEARCH_INDEXES` in your `settings.py` file to define your search indexes:

```
SEARCH_INDEXES = {
    'perfdata': {
        'name': 'Performance Data Portal',
        'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
    }
}
```

For the above:

* The key (`perfdata` above) is used to construct the URL for Search Records.
* `name` can be arbitrary, and is used by templates.
* `uuid` is the UUID of the Globus Search index you are using.


### Configure Facets

Search facets enable users to drill down to specific categories in their search
terms. You can configure them in the `facets` key of your index:

```
SEARCH_INDEXES = {
    'perfdata': {
        ...
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
            }
        ],
        'filter_match': 'match-all',
    }
}
```

* `facets.name` -- The title for this category of facet
* `facets.field_name` -- Field in your Globus Search results to facet
* `facets.type` -- must be one of 'terms', 'numeric_histogram' or 'date_histogram'
* `facets.size` -- configure behavior of returned facets
    * `terms` -- limits the number of buckets returned by Globus Search
    * `histogram` -- number of intervals to create between 'low' and 'high'
* `facets.histogram_range` -- The low and high bounds to set for this facet
* `filter_match` -- Configure match filtering on this index, can be 'match-all' or 'match-any'
    * This setting corresponds to facets that use 'terms'. Facets that use histograms require
        the filter type of 'range'
    * You can also set this globally in settings.py with `DEFAULT_FILTER_MATCH = 'match-all'`


See more options at the [Globus Search Documentation](https://docs.globus.org/api/search/schemas/GFacet/)

### Configure Fields

`fields` are how you define interactive data in the portal. If you want to expose
files for Globus Transfer, you can specify the field `remote_file_manifest`, which
tells the portal to search for `remote_file_manifest` in all incoming search records


SEARCH_INDEXES = {
    'perfdata': {
        ...
        'fields': [
            'remote_file_manifest',
            ('all_the_files', 'remote_file_manifest'),  # if your index's field name is different
        ],

    }
}

You have now enabled file transfer on the `perfdata` index. Users can now transfer data relating
to records from the `detail-transfer/` page.

### Built-in Fields

The following fields are built-in:

* `remote_file_manifest` -- Transfer data in a search record. See [here](https://github.com/fair-research/bdbag/blob/master/doc/config.md#remote-file-manifest)
 for how to format in your search records. Only supports Globus URLs (Example globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt)
* `globus_http_endpoint` -- Endpoint to use for detail-preview page
    * Example: `b4eab318-fc86-11e7-a5a9-0a448319c2f8.petrel.host`
* `globus_http_scope` -- Resource server to use for detail-preview page
    * Example: `petrel_https_server`
* `globus_http_path` -- Path on remote endpoint to use for fetching data on detail-preview page
    * Example: `/ORNL/iozone/iozone_log_ccs_dtn01_atlas1_10G_default.txt`
* `globus_group` -- Typically a Search Records restricted `visible_to` group on Globus Search. List the group here so users can be directed to join to request access when using preview/transfer/etc.
    * Example: `50b6a29c-63ac-11e4-8062-22000ab68755`

### Custom Fields

You can specify any field you want to in `fields`. Examples are the following:

```
SEARCH_INDEXES = {
    'perfdata': {
        ...
        'fields': [
            'subject'
            'publication_year',
            'contributors',
            'authors'
            ('organization', 'field_name_which_lists_organization_and_is_not_politely_named_in_search_records'),
            ('creation_date', lambda x: x[0]['my_record_data']['foo']['bar']['creation_date'])
        ],
    }
}
```

Add an entry to fields any time you want the portal to rely on search data. This makes it easy for
your custom views and templates to refer to things in your search index.


### Custom Templates

Custom templates follow Django's model for templates, with some minor differences
for configuring how they are supposed to look for each index. Start by ensuring they
are setup for your portal:

In `settings.py`
```
SEARCH_INDEXES = {
    'perfdata': {
        ...
        'template_override_dir': 'perfdata',
    }
}

TEMPLATES = [
    {
        'DIRS': [
            os.path.join(BASE_DIR, 'myproject', 'templates'),
        ],
    }
]
```


`TEMPLATES` specifies the Django folder where your templates are stored. For each index,
you can also define `template_override_dir` for overriding templates for _only that index_. It's
possible to have the following layout:

```
myproject/
    templates/
        astronomy/
            components/
                detail-nav.html
                search-facets.html
                search-results.html
            search.html
            detail-overview.html
            detail-transfer.html
        climatology/
            components/
                search-results.html
        neurology/
            components/
                detail-nav.html
                search-results.html
            my-custom-page.html
```

### Example: Tying it all together -- Improving our Dates


In this example, dates are static. Let's make them into python datetimes for more
flexibility.

Start with ensuring the basics in `settings.py`:

```
SEARCH_INDEXES = {
    'perfdata': {
        'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
        'fields': [
            'perfdata',
        ]
    }
}

# This enables extended search debugging
DEBUG = True
INTERNAL_IPS = (
    '127.0.0.1',
)
```

Run the server and login. Basic dates should show up for you.

Now lets add the code for turning dates in `perfdata` into django datetimes. Add
the following code to your settings.py:

```
from datetime import datetime
def perfdata_mapper(search_result):
    dates = search_result[0]['perfdata'].get('dates')
    if dates:
        formatted = [datetime.strptime(d['value'], '%Y-%m-%d') for d in dates]
        search_result[0]['perfdata']['dates'] = formatted
    return search_result[0]
```

And enable it by changing `perfdata` to a tuple:
```
SEARCH_INDEXES = {
    'perfdata': {
        'name': 'Performance Data Portal',
        'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
        'fields': [
            ('perfdata', perfdata_mapper),
        ]
    }
}
```

Now we can edit the template to display our new date. Ensure you have templates
setup:


```
SEARCH_INDEXES = {
    'perfdata': {
        'name': 'Performance Data Portal',
        'uuid': '5e83718e-add0-4f06-a00d-577dc78359bc',
        'fields': [
            ('perfdata', perfdata_mapper),
        ],
        'template_override_dir': 'perfdata',
    }
}

TEMPLATES = [
    {
        'DIRS': [
            os.path.join(BASE_DIR, 'myproject', 'templates'),
        ],
        ...
    }
]
```

`myproject/templates/perfdata/components/search-results.html`
```
<h2>Search Results</h2>
<div id="search-result" class="search-result">
  {% for result in search.search_results %}
  <div class="result-item">

    <h3 class="search-title mt-3">
      <a href="{% url 'detail' globus_portal_framework.index result.subject %}" title="{{result.title|default:'Result'}}">{{result.title|default:'Result'}}</a>
    </h3>

    <div class="result-fields">
      <strong>Date:
      {% for date in result.perfdata.perfdata.dates %}
        {{date}}
      {{date.value}}<br>
      {% endfor %}
      </strong>
    </div>

  </div>
  {% endfor %}
</div>
```

## Developer Install

Clone and run the App locally:

```
    $ git clone https://github.com/globusonline/django-globus-portal-framework
    $ cd django-globus-portal-framework
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
```

Remember to add your Globus credentials. You can put them in
`django_globus_portal_framework/local_settings.py` to avoid accidentally committing them.

```
    SOCIAL_AUTH_GLOBUS_KEY = '<YOUR APP CLIENT ID>'
    SOCIAL_AUTH_GLOBUS_SECRET = '<YOUR APP SECRET>'
    DEBUG = True
```

Migrate and run with:

    $ python manage.py migrate
    $ python manage.py runserver

The app will be running locally at `http://localhost:8000`

## Deployment

It's a good idea to run through the
[Django Deployment Checklist](https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/)
when deploying.
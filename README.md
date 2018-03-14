# django-globus-portal-framework

A collection of tools for quickly bootstrapping a portal for use with Globus
Tools, including Globus Search, Transfer, Auth, and more! Drop in pre-built
defaults to get started quickly, and easily tweak any component when you
need to do things your way.

## 5 Minute Quick-Start

Let's get started with a simple Globus Search portal.

```
    $ pip install django-admin
    $ pip install -e https://github.com/globusonline/django-globus-portal-framework
    $ django-admin startproject myproject
```

Integrate it into your app in `myproject/settings.py`

```
    INSTALLED_APPS = [
        ...
        # This contains general Globus portal tools
        'django-globus-portal-framework',
        # This contains a search portal we will use for this demo
        'django-globus-portal-framework.search',
    ]
```

Then wire up the search portal in your 'myproject/urls.py'

```
    from django.urls import path, include

    urlpatterns = [
        path('', include('globus_portal_framework.urls')),
    ]
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

After you create your app, add these to 'myproject/settings.py'

```
    SOCIAL_AUTH_GLOBUS_KEY = '<YOUR APP CLIENT ID>'
    SOCIAL_AUTH_GLOBUS_SECRET = '<YOUR APP SECRET>'

    INSTALLED_APPS = [
        ...
        'django-globus-portal-framework',
        'django-globus-portal-framework.search',
        'social_django',
    ]

    MIDDLEWARE = [
        ...
        'social_django.middleware.SocialAuthExceptionMiddleware',
    ]

    AUTHENTICATION_BACKENDS = [
        'globus_portal_framework.auth.GlobusOAuth2',
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

Run migrations and startup your project:

```
    $ python manage.py migrate
    $ python manage.py runserver
```

Now you can login at `http://localhost:8000`

## Customizing Your Portal

Now for the fun stuff, customizing the portal to your specific use case.

### Configure Search Fields

These options dictate which fields will be displayed in search, you can
override them in your settings.py:

```
# The search index in Globus Search
SEARCH_INDEX = 'perfdata'
# Path to the schema defining which facets and fields will be displayed.
SEARCH_SCHEMA = os.path.join(BASE_DIR,
                             'myproject/data/datacite.json')
# A function for preparing search results in template data
SEARCH_MAPPER = ('myproject.utils', 'my_mapper')
# The nested path for search entry data in Globus Search. Typically this is
# the name of the index.
SEARCH_ENTRY_FIELD_PATH = 'perfdata'
```

A common search schema file looks like this:

`myproject/data/myfields.json`
```
{
  "fields": {
    "contributors": {
      "field_title": "Contributors"
    },
    "dates": {
      "field_title": "Dates"
    },
    "titles": {
      "field_title": "Titles"
    }
  },
  "facets": [{
      "name": "Contributor",
      "type": "terms",
      "field_name": "perfdata.contributors.contributor_name",
      "size": 10
    }
  ]
}
```

An example for needing a custom SEARCH_MAPPER would be to parse dates before
they are used within the templates. An example would look like this:


```
    from datetime import datetime
    from globus_portal_framework import default_search_mapper


    def my_mapper(entry, schema):

        fields = default_search_mapper(entry, schema)
        # Dates from my search index are formatted: '2018-12-30'
        # Format them into datetimes for Django templates
        fields['dates'] = [{'value': datetime.strptime(d.get('value'), '%Y-%m-%d')}
                           for d in fields.get('dates', [])]
        return fields
```

We can edit directly how data is displayed by overriding the Django template
for displaying search results.

In `settings.py`
```
TEMPLATES = [
    {
        'DIRS': [
            os.path.join(BASE_DIR, 'myproject', 'templates'),
        ],
    }
]
```

`myproject/templates/components/search-results.html`
```
<h2>Search Results</h2>
<div id="search-result" class="search-result">
  {% for result in search.search_results %}
  <div class="result-item">
    <h3 class="search-title mt-3">
      <a href="{% url 'detail' result.subject %}" title="{{result.fields.title}}">{{result.fields.title.value}}</a>
    </h3>
    <div class="result-fields">
      Contributors: {%for contributor in result.fields.contributors.data%}
                {{contributor.contributor_name}}{% if not forloop.last %},{%endif%}
                {%endfor%}<br>
      <strong>My Custom Date Field:{% for date in result.fields.dates.data %}
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
    $ pip install requirements.txt
    $ echo 'DEBUG = True' > globus_portal_framework/local_settings.py
    $ python manage.py migrate
    $ python manage.py runserver
```

The app will be running locally at `http://localhost:8000`
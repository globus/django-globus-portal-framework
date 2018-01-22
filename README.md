# django-globus-portal-framework

Collate data from Globus Search for easy discovery and transfer

## Install as Django App

Note: _Untested_

You likely already have a Django app and want to pick and choose tools
out of this project to use alongside it. In that case you can install
it like any other Django App:

```
    $ pip install -e https://github.com/globusonline/django-globus-portal-framework
```

Then integrate it into your app. In your Django `settings.py`

```
    INSTALLED_APPS = [
        ...
        django-globus-portal-framework,
    ]
```

Run migrations and startup your project:

```
    $ python manage.py migrate
    $ python manage.py runserver
```

Your server will be running at `http://localhost:8000`.

## Install Standalone

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
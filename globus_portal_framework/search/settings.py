from os.path import join, dirname

from django.conf import settings


FOO = getattr(settings, 'FOO', "default_value")

PROJECT_TITLE = getattr(settings, 'PROJECT_TITLE', 'Globus Portal Framework')
# "perfdata" search index
SEARCH_INDEX = getattr(settings, 'SEARCH_INDEX',
                       '5e83718e-add0-4f06-a00d-577dc78359bc')
SEARCH_MAPPER = getattr(settings, 'SEARCH_MAPPER',
                        ('globus_portal_framework.search.utils',
                         'map_datacite')
                        )
SEARCH_SCHEMA = getattr(settings, 'SEARCH_SCHEMA',
                        join(dirname(__file__), 'data/datacite.json')
                        )

SEARCH_RESULTS_PER_PAGE = getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 10)
SEARCH_MAX_PAGES = getattr(settings, 'SEARCH_MAX_PAGES', 10)

from os.path import join, dirname

from django.conf import settings


# "perfdata" search index
SEARCH_INDEX = getattr(settings, 'SEARCH_INDEX',
                       '5e83718e-add0-4f06-a00d-577dc78359bc')
SEARCH_MAPPER = getattr(settings, 'SEARCH_MAPPER',
                        ('globus_portal_framework', 'default_search_mapper'))
SEARCH_SCHEMA = getattr(settings, 'SEARCH_SCHEMA',
                        join(dirname(__file__), 'data/datacite.json')
                        )
SEARCH_ENTRY_FIELD_PATH = getattr(settings, 'SEARCH_ENTRY_FIELD_PATH',
                                  'perfdata')
# Specify the field containing the title
SEARCH_ENTRY_TITLE = getattr(settings, 'SEARCH_ENTRY_TITLE', 'titles')

SEARCH_RESULTS_PER_PAGE = getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 10)
SEARCH_MAX_PAGES = getattr(settings, 'SEARCH_MAX_PAGES', 10)
# This will be the automatic search query when the user loads the page, if
# they have not submitted their own query or there is no query loaded in the
# session. "*" will automatically search everything, but may not be desirable
# if there is a lot of search data in the index, as searches will take a while
DEFAULT_QUERY = getattr(settings, 'DEFAULT_QUERY', '')
BAG_LIMIT = getattr(settings, 'BAG_LIMIT', 50)

# Changes in Globus Portal Framework


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.


## 0.3.0

- Consolidated search settings into a single object called SEARCH_INDEXES
- Removed the following settings (no longer used)
    - ENTRY_SERVICE_VARS
    - SEARCH_INDEX
    - SEARCH_SCHEMA
    - SEARCH_MAPPER
    - SEARCH_ENTRY_FIELD_PATH
- The extended apps in INSTALLED_APPS are now built-in
    - globus_portal_framework.search
    - globus_portal_framework.transfer
- Added extended-filter-facet-features
- Added range facets/filters
- Added settings for filtering behavior, added tests
- Added better error checking for search queries
- Search filters can now be configured in settings.py
- Custom client loading is now possible for Globus Clients
- portal now catches errors resulting from user defined fields
- Fixed possible error when upgrading from an older version
- Fixed 'setting not defined' error when creating a new project
- Can now proxy HTTP requests for files on Globus endpoint that require authorization
- Removed old Django checks, added checks for Index UUID + tests
- Fixed occational bug generating preview https link
- Added modular templates, so indexes can specify their own set of templates
- Added config based multi index support
- Changed name of 'gauth.py' to 'gclients.py' and moved clients
- Project overhaul: consolidated components into a single app

## 0.2.0

### [0.2.0] - 2018-06-12

- Upgraded to Bootstrap v4
- Added Transfer and Preview


## 0.1.0

### [0.1.0] - 2018-03-02

- Initial Release!
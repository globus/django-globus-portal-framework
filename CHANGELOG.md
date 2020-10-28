# Changes in Globus Portal Framework


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.

## 0.3.17 - 2020-10-28

- Fix bugs in python 3.5
    - Remove F strings and other python 3.6 features


## 0.3.16 - 2020-10-20

- Added broad exception handling on facet_modifiers
    - Catch all exceptions except import exceptions (developer errors)

## 0.3.15 - 2020-10-09

- Added 'facet_modifiers' field to index config
    - This allows customizing facets before they are rendered in templates, without writing new views.
- Added support for 'value' type facets
    - 'sum' and 'avg' type facets can now be configured
- Added facet fields 'unique_name' and 'type' to facet results
- Added 'filter_type' to each 'bucket' field in facet results

## 0.3.14 - 2020-09-21

- Fixed error on /allowed-groups view when groups could not be fetched from Globus
- Added Globus 'Preview' support
- Added specific "GroupsException" for catching groups-specific exceptions

## 0.3.13 - 2020-09-09

- Fixed Globus API errors on logout
- Added support for new Globus Groups Resource Server name
    - Changed from 04896e9e-b98e-437e-becd-8084b9e234a0 to 'groups.api.globus.org'
    - 0.3.12 will continue to work for groups until September 23rd

## 0.3.12 - 2020-02-25

- Fixed out of order merge to include changes from last release
    - This adds the get_subject fix not properly included

## 0.3.11 - 2020-02-25

- Fixed get_subject not setting the correct format version.
    - This caused get_subject to malfunction after the latest search release

## 0.3.10 - 2020-01-17

- Fixed version string

## 0.3.9 - 2020-01-17

- Added support for several other Globus Search query options in index definitions
    - `boosts` can be directly specified
    - `sort` can be directly specified
    - `advanced` can be turned on or off
    - `bypass_visible_to` can be turned on or off
    - `result_format_version` can be optionally set
- `result_format_version` by default set to `2017-09-01`
- Date Facets and Filters have been added
    - Dates can now be faceted by intervals
        - Year
        - Month
        - Day
        - Hour
        - Minute
        - Second
    - Date searches are automatically setup alongside facets
    - Arbitrary date range searches are also possible
- Added simple date example to DGPF default startup tutorial
- 'filter-match' can now be specified per-facet for term-type facets
- Fixed `is_authenticated` sometimes showing None on server errors

## 0.3.8 - 2019-12-04

- Support Django 3.0, released Dec 2nd
- Removed 404 and 500 handlers in favor of built-ins
    - views were not removed from DGPF, but now call Django built-ins instead
- Fixed bug in context processors with invalid index, resulting in 500s for 404s

## 0.3.7 - 2019-11-25

- Added Globus Groups allowlist based on public Globus Groups API
- Fixed error message when transfer page is used and file does not exist
- Fixed last page in pagination getting cut off

## 0.3.6 - 2019-08-13

- Added register_custom_index function to allow custom developer defined views
- Fixed 'favicon.ico' being treated as an index in some cases for custom views

## 0.3.5 - 2019-08-02

- Fixed template highlighting for active tab on detail page
- Fixed detail templates not properly displaying errors
- Fixed handling of 404 and 500 pages and added builtin templates for each
- Fixed non-index urls being treated as an index and raising errors
    - This fixes the "favicon.ico is not an index" exception
- Fixed a bug if the group set was not set as visible
    - Added custom setting 'SOCIAL_AUTH_GLOBUS_GROUP_JOIN_URL'
    - Custom setting can be used for private groups or a custom url

## 0.3.4 - 2019-07-15

- Fixed possible error for users navigating to custom dgpf template views after logout
- Fixed logout 'next' query param, custom logout redirects can now be specified in templates

## 0.3.3 - 2019-05-30

- Fixed bug for login redirects when user tokens expired
- Updated README docs

## 0.3.2 - 2019-03-07

- Fixed bug in logout when no scopes were requested
- Changed debugging urls to be optional
- Fixed some things in the README

## 0.3.0 - 2019-03-07

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
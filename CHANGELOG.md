# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.4.11](https://github.com/globus/django-globus-portal-framework/compare/v0.4.10...v0.4.11) (2024-06-17)

### Features

* Add new V3 Templates. Templates will become default in v0.5.x. ([704a86a17786a104372604ed507c22a3d2759758](https://github.com/globus/django-globus-portal-framework/commit/704a86a17786a104372604ed507c22a3d2759758))


### Bug Fixes

* Remove un-used validate_token() function ([20e59ff](https://github.com/globus/django-globus-portal-framework/commit/20e59ff11c0f25cbc49215467606f0ef218cf13a))

## [0.4.10](https://github.com/globus/django-globus-portal-framework/compare/v0.4.9...v0.4.10) (2024-04-25)

### Features

* Add support for Django 5 ([53cf6b5](https://github.com/globus/django-globus-portal-framework/commit/53cf6b5897c93520005b91a7e5e94be9910b3a66))
* Add support for python 3.11 ([173533b](https://github.com/globus/django-globus-portal-framework/commit/173533b730a5038da8f8f35a71aba297a49d5f2c))
* Allow logging in with Globus Groups ([27be3e0](https://github.com/globus/django-globus-portal-framework/commit/27be3e032162d4c505cca310f049dcceb57297df))
* Change templates to use CDNs instead of vendored libs ([f85d206](https://github.com/globus/django-globus-portal-framework/commit/f85d2061da2423788ac6f2d7fb816493f9f9caca))


### Bug Fixes

* updates Globus webapp links to use app. subdomain ([fc240c2](https://github.com/globus/django-globus-portal-framework/commit/fc240c266cc03dd7c03909ab94ef0c082f0cea28))
* Drop support for (long ago sunset) Globus SDK v2 ([65b4273](https://github.com/globus/django-globus-portal-framework/commit/65b4273e99041aab0050f615ba28b9d3eeb1417d))

### [0.4.9](https://github.com/globus/django-globus-portal-framework/compare/v0.4.8...v0.4.9) (2023-12-19)

### Changes

* Remove `result_format_version` from search requests
    * This parameter will no longer be accepted by the Globus Search API on March 30th 2024

### [0.4.8](https://github.com/globus/django-globus-portal-framework/compare/v0.4.7...v0.4.8) (2023-03-29)


### Bug Fixes

* Generic views not inline with the default portal search settings ([f372a75](https://github.com/globus/django-globus-portal-framework/commit/f372a753b43e42fb44dd5643476c7885e987a8f9))
* Upgrade internals from legacy search result format to 2019-08-27 ([c58b293](https://github.com/globus/django-globus-portal-framework/commit/c58b2930606aec0c08d807a341a5181e75ded3d0))


### [0.4.7](https://github.com/globus/django-globus-portal-framework/compare/v0.4.6...v0.4.7) (2023-02-02)


### Bug Fixes

* Correct a handful of docstrings and add missing ones ([9bbaed1](https://github.com/globus/django-globus-portal-framework/commit/9bbaed1b734eb02df1d8e3717ff47bb6f8c1609b))


### [0.4.6](https://github.com/globus/django-globus-portal-framework/compare/v0.4.5...v0.4.6) (2023-01-18)


### Features

* Support Django 4 ([269bb7c](https://github.com/globus/django-globus-portal-framework/commit/269bb7ca4070470bbdf3b5093cee53441dd94b14))


### Bug Fixes

* facet modifiers for generic views ([fedc610](https://github.com/globus/django-globus-portal-framework/commit/fedc6107baf05ac44613c351d134f6002aec7206))

### [0.4.5](https://github.com/globus/django-globus-portal-framework/compare/v0.4.4...v0.4.5) (2022-06-03)


### Bug Fixes

* New lazy-imports feature in globus-sdk 3.9 causing error on startup ([d7b909c](https://github.com/globus/django-globus-portal-framework/commit/d7b909c72459bd5faca74c5e1d2bee71e2976be4))

### [0.4.4](https://github.com/globus/django-globus-portal-framework/compare/v0.4.3...v0.4.4) (2022-05-05)


### Features

* Add support for python 3.10 ([348b35e](https://github.com/globus/django-globus-portal-framework/commit/348b35ed5ddd2ef95e5ee32a20ec817959cdf857))


### Bug Fixes

* Exception handling for SDK v3 during logout ([f46c703](https://github.com/globus/django-globus-portal-framework/commit/f46c7032ddf3d78fa03a4d82f3bbe98712b2dff1))
* regression in Globus SDK v2 for login ([593ed4a](https://github.com/globus/django-globus-portal-framework/commit/593ed4a50ddcb13ef4c5502d6740e7315bd52bb2))

### [0.4.3](https://github.com/globus/django-globus-portal-framework/compare/v0.4.2...v0.4.3) (2022-02-08)


### Bug Fixes

* Login for Globus SDK v3.3.x ([20e8231](https://github.com/globus/django-globus-portal-framework/commit/20e82311436a64d06facf01b27cb75095ec978b4))

### [0.4.2](https://github.com/globus/django-globus-portal-framework/compare/v0.4.1...v0.4.2) (2021-10-15)

### [0.4.1](https://github.com/globus/django-globus-portal-framework/compare/v0.4.0...v0.4.1) (2021-10-15)


### Bug Fixes

* Small fixes and changes to the Getting Started docs ([da202a4](https://github.com/globus/django-globus-portal-framework/commit/da202a4d64061e419b70af8547b4affa423a5064))

## [0.4.0](https://github.com/globus/django-globus-portal-framework/compare/v0.3.22...v0.4.0) (2021-10-11)


### ⚠ BREAKING CHANGES

* Switch to newer v2 templates

### Features

* Add Generic Search and Detail Views ([b8ae79d](https://github.com/globus/django-globus-portal-framework/commit/b8ae79d5620097182fdf27510dfc469ae0087b85))
* Add new v2 portal templates ([b09c957](https://github.com/globus/django-globus-portal-framework/commit/b09c957531f1b32aa04021b6ddfc682572f504c9))
* Added empty classes to differentiate base/search/detail navs ([fdca94d](https://github.com/globus/django-globus-portal-framework/commit/fdca94d8f26052266206b665ff4ee123554b62f6))
* Allow setting template base for backwards compatibility ([f889da7](https://github.com/globus/django-globus-portal-framework/commit/f889da7ebe07d18cf6cd24b4799d9b9c83739773))
* CSS easier to change for site-wide branding ([06d1da2](https://github.com/globus/django-globus-portal-framework/commit/06d1da24423a5a77550f15bf66e880bb20b4b8a7))


### Bug Fixes

* "Demo" index not showing up on first time install for Globus Portal Framework ([3824ec9](https://github.com/globus/django-globus-portal-framework/commit/3824ec9dac5c635e8e8c23caa4dfbb0a0ec2bb8a))
* Clarified error message if token for users are not found ([4813b86](https://github.com/globus/django-globus-portal-framework/commit/4813b86015e73e482197c4fb985a58b876b99a84))
* Fix avg/sum search facets ([49a868a](https://github.com/globus/django-globus-portal-framework/commit/49a868ad127284d247ecfcde7920598eb65f6f09))
* get_subject compatibility with Globus SDK v3 ([4810708](https://github.com/globus/django-globus-portal-framework/commit/4810708697cc47674337ae47efab4ecd41d11bf9))
* Globus png base-nav static URL ([894b426](https://github.com/globus/django-globus-portal-framework/commit/894b4266d6cd858edca8072f1d41cb77533ae247))


* Switch to newer v2 templates ([1c04a6f](https://github.com/globus/django-globus-portal-framework/commit/1c04a6fac1f27a043ea55ec765a4a92837c588d7))
    * New default on per-index setting `'base_templates': 'globus-portal-framework/v2/'`
    * Old templates can still be configured by setting `'base_templates': ''` on the index.



### [0.3.24](https://github.com/globusonline/django-globus-portal-framework/compare/v0.3.23...v0.3.24) (2021-09-28)


### Bug Fixes

* bump version ([dc1071f](https://github.com/globusonline/django-globus-portal-framework/commit/dc1071f83d3221d99a3fe33e4cba5caf4d4e0cd1))

### [0.3.23](https://github.com/globusonline/django-globus-portal-framework/compare/v0.3.22...v0.3.23) (2021-09-28)


### Bug Fixes

* pinned Globus SDK v2 ([63e9b86](https://github.com/globusonline/django-globus-portal-framework/commit/63e9b862434bd359f9e986442da467aa5a967ab3))

## 0.3.22 - 2021-09-03

- Sped up token revocation on logout
- Fixed Bug in Python Social Auth v4 for Globus Backend.
- Fixed Possible mishandling of AuthForbidden exception
- Fixed compatibility for Globus SDK v3

## 0.3.21 - 2021-03-12

- Pinned social-auth-core to 3.x.x, which wasn't always set by pinning social-auth-app-django

## 0.3.20 - 2021-03-09

- Pinned social-auth-app-django to 3.x.x due to bug in 4.0.0

## 0.3.19 - 2020-11-30

- Fixed search bug with date facets providing invalid 'size' param, causing searches to error with 400's

## 0.3.18 - 2020-10-29

- Fixed possible ImportError on some systems

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
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

## 0.2.0

### [0.2.0] - 2018-06-12

- Upgraded to Bootstrap v4
- Added Transfer and Preview


## 0.1.0

### [0.1.0] - 2018-03-02

- Initial Release!
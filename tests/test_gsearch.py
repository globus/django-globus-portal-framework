import pytest
from unittest import mock
from urllib.parse import quote_plus
import tests
from tests import mocks

from globus_portal_framework.gsearch import (
    post_search, get_index, get_pagination, get_filters,
    process_search_data, get_facets, get_search_filters,
    get_date_range_for_date, get_search_query, parse_filters,
    prepare_search_facets, serialize_gsearch_range, deserialize_gsearch_range,
    get_facet_filter_type,
)
import globus_portal_framework.modifiers.facets
from globus_portal_framework.exc import (
    IndexNotFound, GlobusPortalException, InvalidRangeFilter,
)


def mock_modifier():
    pass


@pytest.fixture
def mock_gs_facets():
    return {
        "facet_results": [
            {
                '@datatype': 'GFacetResult',
                '@version': '2017-09-01',
                'name': 'facet_def_0_perfdata.things.i.got',
                'buckets': [
                    {
                        '@datatype': 'GBucket',
                        '@version': '2017-09-01',
                        'count': 99,
                        'value': 'Problems'
                    },
                ],
            },
            {

                '@datatype': 'GFacetResult',
                '@version': '2017-09-01',
                'name': 'facet_def_1_remote_file_manifest.length',
                'buckets': [
                    {
                        '@datatype': 'GBucket',
                        '@version': '2017-09-01',
                        'count': 1,
                        'value': {'from': 18000.0, 'to': 19500.0}
                    },
                ],
            },
            {
                '@datatype': 'GFacetResult',
                '@version': '2017-09-01',
                'name': 'facet_def_2_perfdata.dates.value',
                'buckets': [
                    {
                        '@datatype': 'GBucket',
                        '@version': '2017-09-01',
                        'count': 1,
                        'value': '2017-01'
                    },
                ],
            },
            {
                '@datatype': 'GFacetResult',
                '@version': '2017-09-01',
                'name': 'facet_def_3_remote_file_manifest.length',
                'value': 1835339736.675
            },
            {
                '@datatype': 'GFacetResult',
                '@version': '2017-09-01',
                'name': 'facet_def_4_remote_file_manifest.length',
                'value': 73413589467.0
            },
        ]
    }


@pytest.fixture
def mock_portal_facets():
    return [
        {
            'name': 'Things I Got',
            'field_name': 'things.i.got',
            'size': 10
        },
        {
            'name': 'File Size (Bytes)',
            'type': 'numeric_histogram',
            'field_name': 'remote_file_manifest.length',
            'size': 10,
            'histogram_range': {'low': 15000, 'high': 30000},
        },
        {
            "name": "Dates",
            "field_name": "dates.value",
            "type": "date_histogram",
            "date_interval": "month",
        },
        {
            'name': 'File Size Average',
            'field_name': 'remote_file_manifest.length',
            'type': 'avg',
        },
        {
            'name': 'Total Size (current search)',
            'field_name': 'remote_file_manifest.length',
            'type': 'sum',
        },
    ]


SEARCH_INDEXES = {'myindex': {
    # Randomly generated and not real
    'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
}}


def test_get_index(settings):
    settings.SEARCH_INDEXES = {'foo': {}}
    assert get_index('foo') == {}


def test_post_search_invalid_args(settings):
    settings.SEARCH_INDEXES = {'foo': {'uuid': 'foo_uuid'}}
    empty = {'search_results': [], 'facets': []}
    assert post_search(None, '*', [], user=None, page=1) == empty
    assert post_search('foo', None, [], user=None, page=1) == empty


def test_post_search_basic(settings, search_client_inst, globus_response):
    settings.SEARCH_INDEXES = {'foo': {'uuid': 'foo_uuid'}}
    globus_response.data = mocks.MOCK_EMPTY_SEARCH
    search_client_inst.post_search.return_value = globus_response
    post_search('foo', '*', [], user=None, page=1)
    assert search_client_inst.post_search.called


def test_post_search_search_500_error(settings, search_client_inst,
                                      search_api_error):
    settings.SEARCH_INDEXES = {'foo': {'uuid': 'foo_uuid'}}
    search_client_inst.post_search.side_effect = search_api_error
    result = post_search('foo', '*', [], user=None, page=1)
    assert 'error' in result


def test_post_search_search_dgpf_error(settings, search_client_inst,
                                       search_api_error):
    settings.SEARCH_INDEXES = {'foo': {'uuid': 'foo_uuid'}}
    search_client_inst.post_search.side_effect = search_api_error
    search_api_error.http_status = 400
    result = post_search('foo', '*', [], user=None, page=1)
    assert 'error' in result


def test_get_index_raises_error_on_nonexistent_index():
    with pytest.raises(IndexNotFound):
        get_index('foo')


def test_process_search_data_with_no_records():
    mappers, results = [], []
    data = process_search_data(mappers, results)
    assert data == []


def test_process_search_data_zero_length_content(mock_data):
    sub = mock_data['search']['gmeta'][0]
    sub['content'] = []
    mappers, results = [], [sub]
    data = process_search_data(mappers, results)
    assert data == []


def test_process_search_data_with_one_entry(mock_data):
    sub = mock_data['search']['gmeta'][0]
    mappers, results = [], [sub]
    data = process_search_data(mappers, results)[0]
    assert quote_plus(sub['subject']) == data['subject']
    assert sub['content'] == data['all']


def test_process_search_data_string_field(mock_data):
    sub = mock_data['search']['gmeta'][0]
    sub['content'][0]['foo'] = 'bar'
    mappers, results = ['foo'], [sub]
    data = process_search_data(mappers, results)[0]
    assert data['foo'] == 'bar'


def test_process_search_data_func_field(mock_data):
    sub = mock_data['search']['gmeta'][0]
    sub['content'][0]['foo'] = 'bar'
    mappers = [('foo', lambda x: x[0].get('foo').replace('b', 'c'))]
    results = [sub]
    data = process_search_data(mappers, results)[0]
    assert data['foo'] == 'car'


def test_process_search_data_string_field_missing(mock_data):
    sub = mock_data['search']['gmeta'][0]
    sub['content'][0]['foo'] = 'bar'
    mappers, results = ['foo'], [sub]
    data = process_search_data(mappers, results)[0]
    assert data['foo'] == 'bar'


def test_pagination():
    assert get_pagination(1000, 0)['current_page'] == 1
    assert get_pagination(1000, 10)['current_page'] == 2
    assert get_pagination(1000, 20)['current_page'] == 3
    assert len(get_pagination(1000, 0)['pages']) == 10


def test_get_filters():
    r = get_filters({'titles': ['foo']})
    assert len(r) == 1
    assert r[0]['type'] == 'match_all'

    r = get_filters({'titles': ['foo', 'bar']})
    assert len(r) == 1


@pytest.mark.parametrize('query,expected_filter', [
    ('/?q=*&filter.foo=bar', [{
        'field_name': 'foo',
        'type': 'match_all',
        'values': ['bar']}]
     ),
    ('/?q=*&filter-match-any.foo=bar', [{
        'field_name': 'foo',
        'type': 'match_any',
        'values': ['bar']}]
     ),
    ('/?q=*&filter-match-all.foo=bar', [{
        'field_name': 'foo',
        'type': 'match_all',
        'values': ['bar']}]
     ),
    ('/?q=*&page=1&filter-year.foo=2018', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-01-01 00:00:00',
                    'to': '2019-01-01 00:00:00'}]}]
     ),
    ('/?q=*&page=1&filter-month.foo=2018-01', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-01-01 00:00:00',
                    'to': '2018-01-31 00:00:00'}]}]
     ),
    ('/?q=*&page=1&filter-day.foo=2018-08-13', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-08-13 00:00:00',
                    'to': '2018-08-14 00:00:00'}]}]
     ),
    ('/?q=*&page=1&filter-day.foo=2018-08-13+12:50:03', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-08-13 00:00:00',
                    'to': '2018-08-14 00:00:00'}]}]
     ),
    ('/?q=*&page=1&filter-hour.foo=2018-02-27+23:31:07', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-02-27 23:00:00',
                    'to': '2018-02-27 23:59:59'}]}]
     ),
    ('/?q=*&page=1&filter-minute.foo=2018-03-28+23:31:07', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-03-28 23:31:00',
                    'to': '2018-03-28 23:31:59'}]}]
     ),
    ('/?q=*&page=1&filter-second.foo=2018-03-28+23:31:07', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': '2018-03-28 23:31:06',
                    'to': '2018-03-28 23:31:08'}]}]
     ),
    ('/?q=*&filter-range.foo=1--2', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': 1, 'to': 2}]}]
     ),
    ('/?q=*&filter-range.foo=1.5--2.9', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': 1.5, 'to': 2.9}]}]
     ),
    ('/?q=*&page=1&filter-range.foo=100--*', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': 100, 'to': '*'}]}]
     ),
    ('/?q=*&page=1&filter-range.foo=100--*', [{
        'field_name': 'foo',
        'type': 'range',
        'values': [{'from': 100, 'to': '*'}]}]
     ),
])
def test_get_search_filters(query, expected_filter, rf):
    # list of tests urls and expected outputdicts
    r = rf.get(query)
    filters = get_search_filters(r)
    assert filters == expected_filter


def test_get_search_query(rf):
    r = rf.get('/?q=coffee+and+chocolate')
    assert get_search_query(r) == 'coffee and chocolate'


def test_get_facets(mock_gs_facets, mock_portal_facets, globus_response):
    globus_response.data = mock_gs_facets
    r = get_facets(globus_response, mock_portal_facets, {})
    assert len(r) == 5
    facet = r[0]
    assert set(facet.keys()) == {'name', 'buckets', 'size', 'type',
                                 'field_name', 'unique_name'}
    bucket = facet['buckets'][0]
    assert set(bucket.keys()) == {
        'count', 'value', 'field_name', 'checked', 'filter_type',
        'search_filter_query_key', 'datetime'}
    # No filters defined in third argument, this should not be 'checked'
    assert bucket['checked'] is False


def test_facet_terms_checked(mock_gs_facets, mock_portal_facets,
                             globus_response, rf):
    globus_response.data = mock_gs_facets
    request = rf.get('/?filter.things.i.got=Problems')
    filters = get_search_filters(request)
    r = get_facets(globus_response, mock_portal_facets, filters)
    assert r[0]['buckets'][0]['checked'] is True


def test_facet_numeric_checked(mock_gs_facets, mock_portal_facets,
                               globus_response, rf):
    globus_response.data = mock_gs_facets
    request = rf.get(
        '/?filter-range.remote_file_manifest.length=18000.0--19500.0')
    filters = get_search_filters(request)
    r = get_facets(globus_response, mock_portal_facets, filters)
    # "dates" is the third defined facet [2], with the first bucket checked
    assert r[1]['buckets'][0]['checked'] is True


def test_facet_date_checked(mock_gs_facets, mock_portal_facets,
                            globus_response, rf):
    globus_response.data = mock_gs_facets
    request = rf.get('/?filter-month.dates.value=2017-01')
    filters = get_search_filters(request)
    r = get_facets(globus_response, mock_portal_facets, filters)
    # "dates" is the third defined facet [2], with the first bucket checked
    assert r[2]['buckets'][0]['checked'] is True


def test_get_facet_with_modifiers(mock_gs_facets, mock_portal_facets,
                                  globus_response, monkeypatch):
    globus_response.data = mock_gs_facets
    monkeypatch.setattr(tests.test_gsearch, 'mock_modifier', mock.Mock())
    mock_mods = ['tests.test_gsearch.mock_modifier']
    get_facets(globus_response, mock_portal_facets, [],
               filter_match=None, facet_modifiers=mock_mods)
    assert mock_modifier.called


def test_default_get_facet_with_modifiers(mock_gs_facets, mock_portal_facets,
                                          globus_response, monkeypatch):
    globus_response.data = mock_gs_facets
    mock_drop_empty = mock.Mock()
    monkeypatch.setattr(globus_portal_framework.modifiers.facets,
                        'drop_empty', mock_drop_empty)
    get_facets(globus_response, mock_portal_facets, [],
               filter_match=None, facet_modifiers=None)
    assert mock_drop_empty.called


def test_default_get_facet_with_no_modifiers(mock_gs_facets, mock_portal_facets,
                                             globus_response, monkeypatch):
    globus_response.data = mock_gs_facets
    mock_drop_empty = mock.Mock()
    monkeypatch.setattr(globus_portal_framework.modifiers.facets,
                        'drop_empty', mock_drop_empty)
    get_facets(globus_response, mock_portal_facets, [],
               filter_match=None, facet_modifiers=[])
    assert mock_drop_empty.called is False


def test_facet_modifiers_raise_import_errors(mock_gs_facets, mock_portal_facets,
                                             globus_response):
    globus_response.data = mock_gs_facets
    with pytest.raises(ImportError):
        get_facets(globus_response, mock_portal_facets, [],
                   filter_match=None, facet_modifiers=['does.not.exist'])


def test_facet_modifiers_do_not_raise_non_import_exceptions(
        mock_gs_facets, mock_portal_facets, globus_response, monkeypatch):
    globus_response.data = mock_gs_facets
    exc_mod = mock.Mock(side_effect=Exception())
    monkeypatch.setattr(tests.test_gsearch, 'mock_modifier', exc_mod)
    mock_mods = ['tests.test_gsearch.mock_modifier']
    get_facets(globus_response, mock_portal_facets, [],
               filter_match=None, facet_modifiers=mock_mods)
    assert exc_mod.called


def test_invalid_date_range_type():
    with pytest.raises(GlobusPortalException):
        get_date_range_for_date('2018-02-02', 'fortnight')


def test_invalid_date_range_with_valid_type():
    with pytest.raises(InvalidRangeFilter):
        get_date_range_for_date('not a valid date', 'day')


def test_parse_valid_term_filter_match_all():
    tfilters = ['application/x-hdf', 'image/png']
    assert parse_filters(tfilters, 'filter_match_all') == tfilters


def test_parse_valid_term_filter_match_any():
    tfilters = ['application/x-hdf', 'image/png']
    assert parse_filters(tfilters, 'filter_match_any') == tfilters


def test_parse_valid_range_filters():
    valid_filters = (
        (['2019-10-25 16:43:00'], 'day'),
        (['2019-10-25 16:43:00--2019-10-25 16:43:00'], 'range'),
        (['1--100'], 'range'),
    )
    for rfilter, filter_type in valid_filters:
        search = parse_filters(rfilter, filter_type)
        assert len(search) == 1
        assert set(search[0].keys()) == {'from', 'to'}


def test_invalid_range_filters():
    r = parse_filters(['not_a_valid_range'], 'range')
    assert r == []


def test_prepare_search_facets_valid():
    assert prepare_search_facets([{
            'field_name': 'foo.bar.baz'
        }]) == [{
            'field_name': 'foo.bar.baz',
            'name': 'facet_def_0_foo.bar.baz',
            'type': 'terms',
            'size': 10
        }]


def test_prepare_search_facets_extra_items():
    assert prepare_search_facets([{
            'field_name': 'foo.bar.baz',
            'thick_but_beloved_superheroes': 'The Tick'
        }]) == [{
            'field_name': 'foo.bar.baz',
            'name': 'facet_def_0_foo.bar.baz',
            'type': 'terms',
            'size': 10
        }]


def test_prepare_search_facets_invalid_list():
    # Invalid, should be list of dicts
    with pytest.raises(ValueError):
        prepare_search_facets({'field_name': 'foo'})


def test_prepare_search_facets_missing_field():
    # invalid, should at least define 'field_name'
    with pytest.raises(ValueError):
        prepare_search_facets([{}])


def test_serialize_gserach_range_string():
    range = serialize_gsearch_range({'from': 'min_value', 'to': 'max_value'})
    assert range == 'min_value--max_value'


def test_serialize_gsearch_range_ints():
    assert serialize_gsearch_range({'from': 0, 'to': 10}) == '0--10'


def test_deserialize_gsearch_range_no_separator():
    with pytest.raises(InvalidRangeFilter):
        deserialize_gsearch_range('no-separator-in-range')


def test_deserialize_gsearch_range_missing_low():
    with pytest.raises(InvalidRangeFilter):
        deserialize_gsearch_range('--missing-low-bounds')


def test_deserialize_gsearch_range_missing_high():
    with pytest.raises(InvalidRangeFilter):
        deserialize_gsearch_range('missing-high-bounds--')


@pytest.mark.parametrize('facet_definition,filter_type', [
        # Match all, match any 'terms' filters
        ({'field_name': 'foo.defaults.to.terms'}, 'match-all'),
        ({'field_name': 'foo.match-all',
          'filter_type': 'match-all'}, 'match-all'),
        ({'field_name': 'foo.match-any', 'filter_type': 'match-any'},
         'match-any'),

        # Numeric histograms
        ({'field_name': 'foo.num.hist', 'type': 'numeric_histogram'},
         'range'),

        # Dates
        ({'field_name': 'foo.date.hist', 'type': 'date_histogram',
         'date_interval': 'day'}, 'day'),
        ({'field_name': 'foo.date.hist', 'type': 'date_histogram',
          'date_interval': 'month'}, 'month'),
        ({'field_name': 'foo.date.hist', 'type': 'date_histogram',
          'date_interval': 'year'}, 'year'),

        # Stat facets (Not filterable! Should return None)
        ({'field_name': 'foo.num.sum', 'type': 'avg'}, None),
        ({'field_name': 'foo.num.avg', 'type': 'sum'}, None),
])
def test_get_facet_filter_type_valid(facet_definition, filter_type):
    assert get_facet_filter_type(facet_definition) == filter_type


def test_get_facet_filter_type_invalid_filter():
    assert get_facet_filter_type({'field_name': 'foo', 'type': ''}) is None

import pytest
from globus_portal_framework.exc import IndexNotFound
from unittest import mock

from django.urls import reverse, path
from django.http import HttpResponse
import tests

from tests.mocks import rebuild_index_urlpatterns

from globus_portal_framework.urls import (search_urlpatterns,
                                          register_custom_index,
                                          urlpatterns as dgpf_urlpatterns)

urlpatterns = []


@pytest.fixture
@pytest.mark.urls('tests.test_urls')
def register_patterns(settings):
    SEARCH_INDEXES = {
        'myindex': {
            # Randomly generated and not real
            'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
        },
        'my_custom_index': {
            # Randomly generated and not real
            'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
        }
    }
    settings.SEARCH_INDEXES = SEARCH_INDEXES
    register_custom_index('my_custom_index', ['my_custom_index'])

    urlpatterns = rebuild_index_urlpatterns(
        search_urlpatterns + dgpf_urlpatterns,
        list(SEARCH_INDEXES.keys()))
    custom_search = mock.Mock(
        return_value=HttpResponse('custom_search_view'))
    custom_path = path('<my_custom_index:index>/', custom_search,
                       name='search')
    urlpatterns.insert(0, custom_path)
    setattr(tests.test_urls, 'urlpatterns', urlpatterns)


def test_register_non_existent_index_raises_error(settings):
    settings.SEARCH_INDEXES = {'myindex': {
        # Randomly generated and not real
        'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
    }}
    with pytest.raises(IndexNotFound):
        register_custom_index('foo', ['bar'])


@pytest.mark.urls('tests.test_urls')
def test_custom_search_view(client, register_patterns):
    r = client.get(reverse('search', args=['my_custom_index']))
    assert r.status_code == 200
    assert r.content == b'custom_search_view'


@pytest.mark.urls('tests.test_urls')
def test_regular_search_view_not_affected(client, register_patterns,
                                          mock_data_search):
    r = client.get(reverse('search', args=['myindex']))
    assert r.status_code == 200
    assert b'custom_search_view' not in r.content

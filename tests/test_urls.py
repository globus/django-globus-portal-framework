import pytest
from globus_portal_framework.exc import IndexNotFound
from unittest import mock

from django.urls import reverse, path
from django.http import HttpResponse

from globus_portal_framework.urls import register_custom_index

urlpatterns = [
    path('<index>/foo/bar', lambda r, index: HttpResponse('hello foo'), name='foo')
]

def test_register_non_existent_index_raises_error(settings):
    settings.SEARCH_INDEXES = {'myindex': {
        # Randomly generated and not real
        'uuid': '1e0be00f-8156-499e-980d-f7fb26157c02'
    }}
    with pytest.raises(IndexNotFound):
        register_custom_index('foo', ['bar'])


@pytest.mark.urls('tests.test_urls')
def test_custom_index_converter_view(client):
    r = client.get(reverse('foo', args=['my_custom_index']))
    assert r.status_code == 200
    assert r.content == b'hello foo'

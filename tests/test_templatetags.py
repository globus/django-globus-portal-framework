import pytest
from django.urls import path

from globus_portal_framework.templatetags.is_active import is_active


def view_simple(request):
    pass


def view_complex(request, sun, moon, stars):
    pass


urlpatterns = [
    path('view-simple', view_simple, name='view-simple'),
    path('view-complex/<int:sun>/<int:moon>/<int:stars>/', view_complex,
         name='view-complex')
]


@pytest.mark.urls('tests.test_templatetags')
def test_view_simple(rf):
    r = rf.get('/view-simple')
    assert is_active(r, 'view-simple') == 'active'


@pytest.mark.urls('tests.test_templatetags')
def test_is_active_inactivated(rf):
    r = rf.get('/view-simple')
    assert is_active(r, 'view-complex') == ''


@pytest.mark.urls('tests.test_templatetags')
def test_is_active_with_kwargs(rf):
    r = rf.get('/view-complex/1/2/3/')
    assert is_active(r, 'view-complex', sun=1, moon=2, stars=3) == 'active'


@pytest.mark.urls('tests.test_templatetags')
def test_is_active_quietly_raises_error(rf):
    """Valid, but will raise warning"""
    r = rf.get('view-complex/1/2/3/')
    assert is_active(r, 'view-complex/', sun=1, moon=2, stars=3) == ''

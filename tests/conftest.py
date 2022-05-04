from unittest.mock import Mock
import pytest
import copy
import globus_sdk
from tests import mocks


@pytest.fixture
def search_client(monkeypatch):
    monkeypatch.setattr(globus_sdk, 'SearchClient', Mock())
    return globus_sdk.SearchClient


@pytest.fixture
def search_client_inst(search_client):
    """Return a search client instance"""
    return search_client.return_value


@pytest.fixture
def transfer_client(monkeypatch):
    monkeypatch.setattr(globus_sdk, 'TransferClient', Mock())
    return globus_sdk.TransferClient


@pytest.fixture
def mock_app(monkeypatch):
    monkeypatch.setattr(globus_sdk, 'ConfidentialAppAuthClient', Mock())
    return globus_sdk.ConfidentialAppAuthClient


@pytest.fixture
def globus_api_error(monkeypatch) -> globus_sdk.GlobusAPIError:
    monkeypatch.setattr(globus_sdk, 'GlobusAPIError', mocks.MockGlobusAPIError)
    return globus_sdk.GlobusAPIError
    # response = Mock()
    # response.headers = []
    # response.status_code = 401
    # gapie = globus_sdk.GlobusAPIError(response)
    # return gapie


@pytest.fixture
def search_api_error(monkeypatch) -> globus_sdk.SearchAPIError:
    monkeypatch.setattr(globus_sdk, 'SearchAPIError', mocks.MockGlobusAPIError)
    return globus_sdk.SearchAPIError


@pytest.fixture
def mock_data():
    print(f'Mock data available: {list(mocks.mock_data.keys())}')
    return copy.deepcopy(mocks.mock_data)


@pytest.fixture
def mock_data_search(search_client_inst, mock_data, globus_response):
    globus_response.data = mock_data['search']
    search_client_inst.post_search.return_value = globus_response
    return search_client_inst


@pytest.fixture
def mock_data_get_subject(search_client_inst, mock_data, globus_response):
    globus_response.data = mock_data['get_subject']
    search_client_inst.get_subject.return_value = globus_response
    return search_client_inst


@pytest.fixture
def globus_response():
    class Response:
        data = {}
    return Response()


@pytest.fixture
def user():
    resource_servers = ['transfer.api.globus.org', 'groups.api.globus.org',
                        'auth.globus.org', 'search.api.globus.org']
    return mocks.mock_user('bob', resource_servers)

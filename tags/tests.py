import lxml.html
import pytest


@pytest.fixture(autouse=True)
def real_db(_django_cursor_wrapper):
    _django_cursor_wrapper.enable()


def test_search(client):
    response = client.get('/search/')
    assert response.status_code == 200

    response = client.get('/search/?q=diabetes')
    assert response.status_code == 200

    dom = lxml.html.fromstring(response.content)
    assert len(dom.cssselect('.search-result')) == 10

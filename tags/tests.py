import lxml.html
import pytest


@pytest.fixture
def real_db(_django_cursor_wrapper):
    _django_cursor_wrapper.enable()


def test_search(client, real_db):
    response = client.get('/search/')
    assert response.status_code == 200

    response = client.get('/search/?q=diabetes')
    assert response.status_code == 200

    dom = lxml.html.fromstring(response.content)
    assert len(dom.cssselect('.search-result')) == 10


def test_annotations_similarity():
    from collections import namedtuple
    from tags.tasks import annotations_similarity

    AnnoMock = namedtuple('AnnoMock', ['sample_id', 'annotation'])
    s = [AnnoMock(1, 'hi'), AnnoMock(2, '')]
    s2 = [AnnoMock(1, 'hi'), AnnoMock(2, 'hi')]
    assert annotations_similarity([s, s]) == 1
    assert annotations_similarity([s, s, s]) == 1
    assert annotations_similarity([s, s2]) == -1/3.0

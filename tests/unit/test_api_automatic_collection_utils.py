import pytest

from api.automaticCollectionUtils import fetchAutomaticCollectionEditions


def test_fetchAutomaticCollectionEditions_mostRecent(mocker):
    dbClient = mocker.MagicMock()
    dbClient.fetchAutomaticCollection.return_value = mocker.MagicMock(
        keyword_query=None,
        author_query=None,
        title_query=None,
        subject_query=None,
        sort_field="date",
        sort_direction="DESC",
        limit=100,
    )
    dbClient.fetchAllPreferredEditions.return_value = (20, mocker.sentinel.sortedEditions)
    total, editions = fetchAutomaticCollectionEditions(
        dbClient,
        mocker.sentinel.collectionId,
        perPage=10,
        page=1,
    )
    assert total == 20
    assert editions == mocker.sentinel.sortedEditions


def test_fetchAutomaticCollectionEditions_searchBased(mocker):
    dbClient = mocker.MagicMock()
    dbClient.fetchAutomaticCollection.return_value = mocker.MagicMock(
        keyword_query=mocker.sentinel.keyword_query,
        author_query=mocker.sentinel.author_query,
        title_query=mocker.sentinel.title_query,
        subject_query=mocker.sentinel.subject_query,
        sort_field="date",
        sort_direction="DESC",
        limit=100,
    )
   dbClient.fetchAllPreferredEditions.return_value = (20, mocker.sentinel.sortedEditions)
    with pytest.raises(ValueError):
        fetchAutomaticCollectionEditions(
            dbClient,
            mocker.sentinel.collectionId,
            perPage=10,
            page=1,
        )

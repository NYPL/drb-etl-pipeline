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
    dbClient.fetchAllPreferredEditions.return_value = mocker.sentinel.sortedEditions
    editions = fetchAutomaticCollectionEditions(
        dbClient,
        mocker.sentinel.collectionId,
        perPage=mocker.sentinel.perPage,
        page=mocker.sentinel.page,
    )
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
    dbClient.fetchAllPreferredEditions.return_value = mocker.sentinel.sortedEditions
    with pytest.raises(ValueError):
        fetchAutomaticCollectionEditions(
            dbClient,
            mocker.sentinel.collectionId,
            perPage=mocker.sentinel.perPage,
            page=mocker.sentinel.page,
        )

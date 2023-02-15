from logger import createLog

logger = createLog(__name__)


def fetchAutomaticCollectionEditions(dbClient, collectionId, page: int, perPage: int):
    """Given a collection id for an automatic collection, perform the given
    search and return a list of collection editions
    """
    automaticCollection = dbClient.fetchAutomaticCollection(collectionId)
    if not automaticCollection:
        logger.warning("Found invalid automatic collection %s with no search definition", collectionId)
        return (0, [])

    nextPageSize = _nextPageSize(automaticCollection.limit, page, perPage)

    # Skip ES and go straight to the DB if there's no actual search to be done
    if not _requiresSearch(automaticCollection):
        (totalCount, editions) = dbClient.fetchAllPreferredEditions(
            sortField=automaticCollection.sort_field,
            sortDirection=automaticCollection.sort_direction,
            page=page,
            perPage=nextPageSize,
        )

    # TODO: Hit ES for query based collections
    else:
        raise ValueError("Automatic collection search is not yet implemented")

    return (min(totalCount, automaticCollection.limit), editions)


def _requiresSearch(automaticCollection) -> bool:
    return any(
        [
            automaticCollection.keyword_query,
            automaticCollection.author_query,
            automaticCollection.title_query,
            automaticCollection.subject_query,
        ],
    )


def _nextPageSize(limit, page, perPage):
    """Given an absolute max limit, a page number, and a standard page
    page size, determine what the next page size fetched should be."""

    # Just fetch the page size if there is not absolute limit
    if not limit:
        return perPage
    offset = (page - 1) * perPage
    # If the next page puts us over the absolute limit, only fetch
    # enough items to hit the limit. Otherwise, fetch a full page
    return min(limit - offset, perPage)

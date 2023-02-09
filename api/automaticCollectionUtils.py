from logger import createLog

logger = createLog(__name__)


def fetchAutomaticCollectionEditions(dbClient, collectionId):
    """Given a collection id for an automatic collection, perform the given
    search and return a list of collection editions
    """
    automaticCollection = dbClient.fetchAutomaticCollection(collectionId)
    if not automaticCollection:
        logger.warning("Found invalid automatic collection %s with no search definition", collectionId)
        return []

    # Skip ES and go straight to the DB if there's no actual search to be done
    if not _requiresSearch(automaticCollection):
        return dbClient.fetchSortedEditions(
            sortField=automaticCollection.sort_field,
            sortDirection=automaticCollection.sort_direction,
            limit=automaticCollection.limit,
        )

    # TODO: Hit ES for query based collections
    raise ValueError("Automatic collection search is not yet implemented")


def _requiresSearch(automaticCollection) -> bool:
    return any(
        [
            automaticCollection.keyword_query,
            automaticCollection.author_query,
            automaticCollection.title_query,
            automaticCollection.subject_query,
        ],
    )

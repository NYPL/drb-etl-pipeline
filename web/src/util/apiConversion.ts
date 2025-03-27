/** Converts API responses to internal types */

import {
  ApiCollectionQuery,
  CollectionQuery,
  CollectionQueryDefaults,
} from "../types/CollectionQuery";
import { Query, SearchField, Sort } from "../types/DataModel";
import {
  ApiSearchQuery,
  Filter,
  SearchQuery,
  SearchQueryDefaults,
} from "../types/SearchQuery";

/**
 * Takes an object of type `ApiSearchQuery` and returns a `SearchQuery` object.
 * This function does not add defaults if they are] not passed.
 *
 * @param apiQuery
 */
export const toSearchQuery = (apiQuery: ApiSearchQuery): SearchQuery => {
  if (!apiQuery.query || apiQuery.query.length < 1) {
    throw new Error("Mising param `queries` in search request ");
  }

  const toQuery = (query: string): Query => {
    //If we are guaranteed that this is one query, the first colon is not part of the search term.  Split only on the first colon
    const separated = query.split(/:(.+)/);

    return {
      field: separated[0] as SearchField,
      query: separated[1],
    };
  };

  /**
   * Because the queries are read directly from URL, this function extracts the queries of form
   * "author:shakespeare, william,title:Macbeth" and returns
   * `[{field: "author", query: "shakespeare, william"}, {field: title, query:Macbeth}]`
   */
  const toQueries = (apiQueries: string): Query[] => {
    // Separating the string by both comma and colon
    // eg: author:shakespeare, william,title:Macbeth becomes [author, :, shakespeare, ,,  william, ,, title, :, Macbeth]
    const separated = apiQueries.split(/(,|:)/);

    // We know that any search term is preceded by a search field followed by a colon.
    // When we find a search field followed by a colon, we return the first index of this search field.
    const keysIndexes = separated
      .map((sep, i) => {
        if (
          Object.values(SearchField).includes(sep as SearchField) &&
          separated[i + 1] === ":"
        ) {
          return apiQueries.indexOf(sep);
        }
      })
      .filter((index) => index !== undefined);

    // Creates an array of strings that each represent a search term
    const stringQueries = keysIndexes.map((keyIndex, i) => {
      // When it is not the last value, there is also a comma after the key:value pair that we must ignore
      return i < keysIndexes.length - 1
        ? apiQueries.substring(keyIndex, keysIndexes[i + 1] - 1)
        : apiQueries.substring(keyIndex);
    });

    return stringQueries.map((query) => {
      return toQuery(query);
    });
  };

  // The front end only sorts by the first Sort.
  const toSorts = (apiSort: string): Sort => {
    const split = apiSort.split(":");
    return { field: split[0], dir: split[1] };
  };

  const toFilters = (apiFilters: string): Filter[] => {
    const separated = apiFilters.split(",");
    const filters: Filter[] = separated.map((sep) => {
      const split = sep.split(":");
      return { field: split[0], value: split[1] };
    });
    return filters;
  };

  return {
    queries: toQueries(apiQuery.query),
    ...(apiQuery.display && { display: toQuery(apiQuery.display) }),
    ...(apiQuery.filter && { filters: toFilters(apiQuery.filter) }),
    ...(apiQuery.page && { page: apiQuery.page }),
    ...(apiQuery.size && { perPage: apiQuery.size }),
    ...(apiQuery.sort && { sort: toSorts(apiQuery.sort) }),
    ...(apiQuery.showAll && {
      showAll: apiQuery.showAll === "true",
    }),
  };
};

const toApiSorts = (sort: Sort): string => {
  return `${sort.field}:${sort.dir}`;
};

/**
 * Converts a searchQuery to send to server.
 * First assigns the `queries` parameter, which must always exist.
 * Then, checks all of the other paramaters to see if they have changed from the default
 * and only sends it if there is no default.
 *
 * @param searchQuery
 */
export const toApiQuery = (searchQuery: SearchQuery): ApiSearchQuery => {
  if (!searchQuery) return;
  if (!searchQuery.queries || searchQuery.queries.length < 1) {
    throw new Error("cannot convert searchQuery with no queries");
  }

  const toApiFilters = (filters: Filter[]): string[] => {
    return filters
      ? filters.map((filter) => {
          return `${filter.field}:${filter.value}`;
        })
      : [];
  };

  const toQuery = (query: Query): string => {
    return `${query.field}:${query.query}`;
  };

  const toApiQueries = (queries: Query[]): string[] => {
    return queries.map((query) => toQuery(query));
  };

  return {
    query: toApiQueries(searchQuery.queries).join(","),
    ...(searchQuery.display && { display: toQuery(searchQuery.display) }),
    ...(searchQuery.filters &&
      searchQuery.filters.length &&
      searchQuery.filters !== SearchQueryDefaults.filters && {
        filter: toApiFilters(searchQuery.filters).join(","),
      }),
    ...(searchQuery.page &&
      searchQuery.page !== SearchQueryDefaults.page && {
        page: searchQuery.page,
      }),
    ...(searchQuery.perPage &&
      searchQuery.perPage !== SearchQueryDefaults.perPage && {
        size: searchQuery.perPage,
      }),
    ...(searchQuery.sort &&
      searchQuery.sort !== SearchQueryDefaults.sort && {
        sort: toApiSorts(searchQuery.sort),
      }),
    ...(searchQuery.showAll !== undefined &&
      typeof searchQuery.showAll !== "undefined" &&
      searchQuery.showAll !== SearchQueryDefaults.showAll && {
        showAll: searchQuery.showAll.toString(),
      }),
  };
};

/**
 * Converts an API query object to a NextJS query object
 * NextJS Router accepts query objects of type { [key: string]: string }
 *
 * @param query
 */
export const toLocationQuery = (
  query: ApiSearchQuery | ApiCollectionQuery
): string => {
  return Object.assign(
    {},
    ...Object.keys(query).map((key) => ({
      [key]: query[key],
    }))
  );
};

/**
 * Converts a collectionQuery to send to server.
 * Checks all of the other paramaters to see if they have changed from the default
 * and only sends it if there is no default.
 *
 * @param collectionQuery
 */
export const toApiCollectionQuery = (
  collectionQuery: CollectionQuery
): ApiCollectionQuery => {
  if (!collectionQuery) return;

  return {
    ...(collectionQuery.page &&
      collectionQuery.page !== CollectionQueryDefaults.page && {
        page: collectionQuery.page,
      }),
    ...(collectionQuery.perPage &&
      collectionQuery.perPage !== CollectionQueryDefaults.perPage && {
        perPage: collectionQuery.perPage,
      }),
    ...(collectionQuery.sort &&
      collectionQuery.sort !== CollectionQueryDefaults.sort && {
        sort: collectionQuery.sort,
      }),
  };
};

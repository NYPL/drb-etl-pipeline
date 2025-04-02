/* eslint-env mocha */
import { SearchField } from "~/src/types/DataModel";
import { ApiSearchQuery, SearchQuery } from "~/src/types/SearchQuery";
import { toApiQuery, toSearchQuery } from "../apiConversion";

// Use require instead of import so that it will cast correctly to `ApiSearchQuery`
// https://github.com/microsoft/TypeScript/issues/11152

import {
  searchQuery as apiQuery,
  emptySearchQuery,
} from "../../__tests__/fixtures/SearchQueryFixture";

/**
 * Unit tests for `ApiConversion.ts`
 * Because ApiQuery is user-editable (based on what a user types in the URL)
 * all of the edge cases must be tested.
 */

const searchQuery: SearchQuery = {
  filters: [
    { field: "language", value: "Spanish" },
    { field: "startYear", value: "1800" },
    { field: "endYear", value: "2000" },
  ],
  page: 3,
  perPage: 20,
  queries: [
    { field: SearchField.Keyword, query: '"Civil War" OR Lincoln' },
    { field: SearchField.Author, query: "last, first" },
  ],
  showAll: true,
  sort: { dir: "asc", field: "title" },
};

describe("Converting api query to search query", () => {
  test("converts api query with maximal searchquery information", () => {
    expect(toSearchQuery(apiQuery)).toEqual(searchQuery);
  });

  test("Takes the first filterYears value when passed more than one year filter", () => {
    const apiQueryExtrayears = Object.assign({}, apiQuery, {
      filter: apiQuery.filter + ",startYear:1900,endYear:2010",
    });

    const searchQueryExtraYears = Object.assign({}, searchQuery, {
      filters: [
        ...searchQuery.filters,
        { field: "startYear", value: "1900" },
        { field: "endYear", value: "2010" },
      ],
    });

    expect(toSearchQuery(apiQueryExtrayears).filters).toEqual(
      searchQueryExtraYears.filters
    );
  });

  test("Converts all 'format' and 'language' filters", () => {
    const apiQueryExtraFilters = Object.assign({}, apiQuery, {
      filter: apiQuery.filter + ",language:english,format:epub,format:pdf",
    });
    const searchQueryExtraFilters = Object.assign({}, searchQuery, {
      filters: [
        ...searchQuery.filters,
        { field: "language", value: "english" },
        { field: "format", value: "epub" },
        { field: "format", value: "pdf" },
      ],
    });
    expect(toSearchQuery(apiQueryExtraFilters).filters).toEqual(
      searchQueryExtraFilters.filters
    );
  });

  test("Throws error when empty api query is passed", () => {
    expect(() => {
      toSearchQuery(emptySearchQuery);
    }).toThrowError("Mising param `queries` in search request");
  });

  test("converts api query with the minimal information", () => {
    const minimalApiQuery: ApiSearchQuery = {
      query: "author:cat",
    };

    const minimalSearchQuery: SearchQuery = {
      queries: [
        {
          field: SearchField.Author,
          query: "cat",
        },
      ],
    };

    expect(toSearchQuery(minimalApiQuery)).toEqual(minimalSearchQuery);
  });
});

describe("Converting search query to api query", () => {
  test("converts searchQuery to apiQuery with maximal information", () => {
    const expectedApiQuery: ApiSearchQuery = {
      filter: "language:Spanish,startYear:1800,endYear:2000",
      size: 20,
      page: 3,
      showAll: "true",
      query: 'keyword:"Civil War" OR Lincoln,author:last, first',
      sort: "title:asc",
    };

    expect(toApiQuery(searchQuery)).toEqual(expectedApiQuery);
  });

  test("converts throws an error when trying to convert searchQuery without queries", () => {
    const emptySearchQuery = Object.assign({}, searchQuery, { queries: [] });
    expect(() => {
      toApiQuery(emptySearchQuery);
    }).toThrow("cannot convert searchQuery with no queries");
  });

  test("converts searchQuery to apiQuery with minimal information", () => {
    const minimalApiQuery: ApiSearchQuery = {
      query: "keyword:cat",
    };
    expect(
      toApiQuery({ queries: [{ field: SearchField.Keyword, query: "cat" }] })
    ).toEqual(minimalApiQuery);
  });
});

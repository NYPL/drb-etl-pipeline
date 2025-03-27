import { ApiSearchQuery } from "~/src/types/SearchQuery";

export const searchQuery: ApiSearchQuery = {
  query: 'keyword:"Civil War" OR Lincoln,author:last, first',
  filter: "language:Spanish,startYear:1800,endYear:2000",
  sort: "title:asc",
  size: 20,
  page: 3,
  showAll: "true",
};

export const emptySearchQuery: ApiSearchQuery = {
  filter: "language:english",
  page: 0,
  query: "",
};

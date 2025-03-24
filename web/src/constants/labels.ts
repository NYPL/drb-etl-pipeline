export const workDetailDefinitionLabels = {
  alt_titles: "Alternative Titles",
  summary: "Summary",
  series: "Series",
  agents: "Author",
  subjects: "Subject",
  language: "Language",
};

export const editionDetailDefinitionLabels = {
  publication_date: "Publication Date",
  publication_place: "Publication Place",
  agents: "Publisher(s)",
  edition_statement: "Edition Statement",
  language: "Language",
  table_of_contents: "Table of Contents",
  extent: "Extent",
  volume: "Volume",
  summary: "Summary",
};

export const allWorkLabels = {
  title: "Title",
  sub_title: "Subtitle",
  alt_titles: "Alternative Titles",
  medium: "Medium",
  series: "Series",
  summary: "Summary",
  agents: "Agents",
  subjects: "Subject",
  dates: "Year of Publication",
  identifiers: "Identifiers",
  links: "Links",
  measurements: "Measurements",
};

const breadcrumbUrls = {
  home: "https://www.nypl.org",
  research: "https://www.nypl.org/research",
  drb: "/",
};

export const breadcrumbTitles = {
  home: "Home",
  research: "Research",
  drb: "Digital Research Books Beta",
  advancedSearch: "Advanced Search",
};

export const defaultBreadcrumbs = [
  { url: breadcrumbUrls.home, text: breadcrumbTitles.home },
  { url: breadcrumbUrls.research, text: breadcrumbTitles.research },
  { url: breadcrumbUrls.drb, text: breadcrumbTitles.drb },
];

export const documentTitles = {
  home: "Digital Research Books Beta | NYPL",
  advancedSearch: "Advanced Search | Digital Research Books Beta | NYPL",
  search: "Search Results | Digital Research Books Beta | NYPL",
  workItem: "Work Details | Digital Research Books Beta | NYPL",
  editionItem: "Edition Details | Digital Research Books Beta | NYPL",
  readItem: "Read Online | Digital Research Books Beta | NYPL",
  collection: "Collection | Digital Research Books Beta | NYPL",
};

export const yearsType = { start: "Start", end: "End" };
export const filtersLabels = {
  show_all: "Available to read now",
  language: "Language",
  format: "Format",
  years: "Publication Year",
};

export const inputTerms = [
  { text: "Keyword", value: "keyword" },
  { text: "Author", value: "author" },
  { text: "Title", value: "title" },
  { text: "Subject", value: "subject" },
];

export const inputTermRows = [
  [
    { key: "keyword", label: "Keyword" },
    { key: "author", label: "Author" },
  ],
  [
    { key: "title", label: "Title" },
    { key: "subject", label: "Subject" },
  ],
];

export const FormatTypes = [
  { value: "readable", label: "Readable" },
  { value: "downloadable", label: "Downloadable" },
  { value: "requestable", label: "Requestable" },
];

export const errorMessagesText = {
  emptySearch: "Error: Please enter a search term",
  invalidDate: "Error: Start date must be before End date",
};

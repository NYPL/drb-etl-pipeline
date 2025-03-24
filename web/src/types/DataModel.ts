/* eslint-disable camelcase */

export type FacetItem = { value?: string; count?: number };

export type Agent = {
  lcnaf?: string;
  name?: string;
  primary?: string;
  viaf?: string;
  roles?: string[];
};

//This Instance is from the instances of the Edition endpoint
export type Instance = {
  authors?: Agent[];
  contributors?: Agent[];
  dates?: Date[];
  extent?: string;
  identifiers?: Identifier[];
  instance_id?: number;
  items?: ApiItem[];
  languages?: Language[];
  publication_place?: string;
  publishers?: Agent[];
  summary?: string;
  table_of_contents?: string;
  title?: string;
};

export type Cover = {
  url: string;
  media_type: string;
  flags: LinkFlags;
};

export type Rights = {
  source?: string;
  license?: string;
  rightsStatement?: string;
};

export type ApiItem = {
  content_type?: string;
  contributors?: Agent[];
  drm?: string;
  item_id?: number;
  links?: ItemLink[];
  location?: string;
  modified?: string;
  measurements?: string;
  rights?: Rights[];
  source?: string;
};

export type EditionCardItem = {
  readOnlineLink: ItemLink;
  downloadLink: ItemLink;
  rights: Rights;
};

export type LinkFlags = {
  catalog: boolean;
  download: boolean;
  reader: boolean;
  edd?: boolean;
  embed?: boolean;
  nypl_login?: boolean;
  fulfill_limited_access?: boolean;
};

export type ItemLink = {
  link_id: number;
  mediaType: string;
  url: string;
  flags: LinkFlags;
};

export type Language = {
  language?: string;
  iso_2?: string;
  iso_3?: string;
};

export type Identifier = {
  authority?: string;
  identifier?: string;
};
export type Date = {
  date: string;
  type: string;
};

export type WorkEdition = {
  date_modified?: string;
  date_created?: string;
  edition_id?: number;
  publication_place?: string;
  publication_date?: string;
  edition?: string;
  edition_statement?: string;
  languages?: Language[];
  links?: ItemLink[];
  volume?: string;
  table_of_contents?: string;
  title?: string;
  extent?: string;
  summary?: string;
  work_id?: number;
  publishers?: Agent[];
  items?: ApiItem[];
  work_uuid?: string;
};

export type Subject = {
  heading?: string;
  authority?: string;
  controlNo?: string;
};

export type Measurement = {
  quantity?: string;
  value?: number;
  weight?: number;
  taken_at?: string;
};

//Refer to sorts.ts
export type Sort = { field: string; dir: string };

export enum SearchField {
  Title = "title",
  Keyword = "keyword",
  Author = "author",
  Viaf = "viaf",
  Subject = "subject",
}

export interface Query {
  query: string;
  field: SearchField;
}

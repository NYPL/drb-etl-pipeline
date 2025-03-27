import { Rights } from "./DataModel";

export type Opds2Feed = {
  facets?: OpdsFacet[];
  groups?: Opds2Feed[];
  images?: OpdsImage[];
  links: OpdsLink[];
  message?: string;
  metadata: OpdsMetadata;
  navigation?: OpdsNavigation[];
  publications?: OpdsPublication[];
};

export type OpdsFacet = {
  links: OpdsLink[];
  metadata: OpdsMetadata;
};

export type OpdsLink = {
  href: string;
  rel: string | string[];
  type: string;
  identifier?:
    | "catalog"
    | "downloadable"
    | "embedable"
    | "readable"
    | "requestable";
};

export type OpdsMetadata = {
  "@type"?: string;
  alternate?: string | string[];
  created?: string;
  creator?: string;
  currentPage?: number;
  description?: string;
  itemsPerPage?: number;
  language?: string;
  locationCreated?: string;
  modified?: string;
  numberOfItems?: number;
  published?: number;
  publisher?: string;
  rights?: Rights;
  sortAs?: string;
  subtitle?: string;
  title: string;
  uuid?: string;
};

export type ReadingOrder = {
  alternate: string;
  bitrate: number;
  children: any[];
  duration: number;
  height: number;
  href: string;
  language: string;
  properties: any;
  rel: string;
  templated: boolean;
  title: string;
  type: string;
  width: number;
};

export type Resource = {
  alternate: string;
  bitrate: number;
  children: any[];
  duration: number;
  height: number;
  href: string;
  language: string;
  properties: any;
  rel: string;
  templated: boolean;
  title: string;
  type: string;
  width: number;
};

export type OpdsNavigation = {
  href: string;
  rel: string;
  title: string;
  type: string;
};

export type OpdsPublication = {
  editions: any[];
  images: OpdsImage[];
  links: OpdsLink[];
  metadata: OpdsMetadata;
  type: string;
};

export type OpdsImage = {
  href: string;
  type: string;
};

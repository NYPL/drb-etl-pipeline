import { Agent, Instance, Language } from "./DataModel";
import { OpdsMetadata } from "./OpdsModel";

export type EditionQuery = {
  editionIdentifier: string;
  showAll?: "true" | "false";
};

export type EditionResult = {
  status?: number;
  timestamp?: string;
  responseType?: string;
  data?: ApiEdition;
};

export type ApiEdition = {
  edition?: string;
  edition_id?: number;
  edition_statement?: string;
  extent?: string;
  inCollections?: OpdsMetadata[];
  instances: Instance[];
  languages?: Language[];
  message?: string;
  publication_date?: string;
  publication_place?: string;
  publishers?: Agent[];
  sub_title?: string;
  summary?: string;
  table_of_contents?: string;
  title?: string;
  volume?: string;
  work_authors?: Agent[];
  work_id?: number;
  work_title?: string;
  work_uuid?: string;
};

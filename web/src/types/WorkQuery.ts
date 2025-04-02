import { Agent, Date, Language, Subject, WorkEdition } from "./DataModel";
import { OpdsMetadata } from "./OpdsModel";

export type WorkQuery = {
  identifier: string;
  recordType?: "editions" | "instances";
  showAll?: "true" | "false";
};

export type WorkResult = {
  status?: number;
  timestamp?: string;
  responseType?: string;
  data?: ApiWork;
};

export type ApiWork = {
  alt_titles?: string[];
  authors?: Agent[];
  contributors?: string[];
  dates?: Date[];
  editions?: WorkEdition[];
  edition_count?: number;
  inCollections?: OpdsMetadata[];
  languages?: Language[];
  measurements?: string[];
  medium?: string;
  message?: string;
  series?: string;
  series_position?: string;
  sub_title?: string;
  subjects?: Subject[];
  title?: string;
  uuid?: string;
};

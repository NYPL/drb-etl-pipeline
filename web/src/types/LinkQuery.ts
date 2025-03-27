import { LinkFlags } from "./DataModel";
import { ApiWork } from "./WorkQuery";

export type LinkResult = {
  data: ApiLink;
  responseType: string;
  status: number;
  timestamp: string;
};

export type ApiLink = {
  content?: string;
  flags: LinkFlags;
  link_id: number;
  media_type: string;
  message?: string;
  url: string;
  work: ApiWork;
};

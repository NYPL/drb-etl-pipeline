import { OpdsMetadata } from "~/src/types/OpdsModel";
import { WorkResult } from "~/src/types/WorkQuery";

const createWorkResult = (inCollections: OpdsMetadata[] = []): WorkResult => {
  return {
    data: {
      alt_titles: ["Alt title 1", "Alt title 2"],
      authors: [
        {
          lcnaf: "",
          name: "McClure, H. David. ()",
          primary: "",
          viaf: "",
        },
      ],
      contributors: [],
      dates: null,
      edition_count: 2,
      editions: [
        {
          edition: null,
          edition_id: 862233,
          edition_statement: null,
          extent: "1 online resource (ix, 254 pages).",
          items: [
            {
              content_type: "ebook",
              contributors: [],
              drm: null,
              item_id: 1280883,
              links: [
                {
                  link_id: 2309913,
                  mediaType: "text/html",
                  url: "catalog.hathitrust.org/api/volumes/oclc/329985.html",
                  flags: {
                    catalog: false,
                    download: false,
                    reader: false,
                    embed: true,
                  },
                },
              ],
              location: null,
              measurements: null,
              modified: null,
              rights: [],
              source: "oclc",
            },
          ],
          languages: [
            {
              iso_2: "en",
              iso_3: "eng",
              language: "English",
            },
            {
              iso_2: "en",
              iso_3: "eng",
              language: "German",
            },
          ],
          links: [
            {
              link_id: 1614426,
              mediaType: "image/jpeg",
              url: "test-cover-1",
              flags: {
                catalog: false,
                download: false,
                reader: false,
                embed: true,
              },
            },
            {
              link_id: 1614426,
              mediaType: "image/jpeg",
              url: "test-cover-2",
              flags: {
                catalog: false,
                download: false,
                reader: false,
                embed: true,
              },
            },
          ],
          publication_date: "1967",
          publication_place: null,
          publishers: [
            {
              lcnaf: "",
              name: "Foreign Service Institute, Dept. of State;",
              viaf: "",
            },
          ],
          summary: null,
          table_of_contents: null,
          title: "Yoruba; intermediate texts ",
          volume: null,
          work_uuid: "15156b66-fe7d-4d83-b96b-c96e25a39338",
        },
        {
          edition: null,
          edition_id: 862232,
          edition_statement: null,
          extent: null,
          items: [
            {
              content_type: "ebook",
              contributors: [
                {
                  lcnaf: "",
                  name: "University of Michigan",
                  roles: ["provider", "responsible"],
                  viaf: "",
                },
                {
                  lcnaf: "",
                  name: "Google",
                  roles: ["digitizer"],
                  viaf: "",
                },
              ],
              drm: null,
              item_id: 1280882,
              links: null,
              location: null,
              measurements: null,
              modified: null,
              rights: [
                {
                  license: "public_domain (us_only)",
                  rightsStatement: "Public Domain when viewed in the US",
                  source: "hathitrust",
                },
              ],
              source: "hathitrust",
            },
          ],
          languages: [
            {
              iso_2: "en",
              iso_3: "eng",
              language: "English",
            },
          ],
          links: [],
          publication_date: "1980",
          publication_place: "District of Columbia",
          publishers: [
            {
              lcnaf: "",
              name: "Foreign Service Institute. Dept. of State",
              viaf: "",
            },
          ],
          summary: null,
          table_of_contents: null,
          title: "Yoruba; intermediate texts",
          volume: null,
          work_uuid: "15156b66-fe7d-4d83-b96b-c96e25a39338",
        },
      ],
      inCollections: inCollections,
      languages: [
        {
          iso_2: "en",
          iso_3: "eng",
          language: "English",
        },
      ],
      measurements: [],
      medium: null,
      series: "The modern library classics",
      series_position: "vol. VIII",
      sub_title: "sub title sub title",
      subjects: [
        {
          authority: "lcgft",
          controlNo: "",
          heading: "Readers (Publications)",
        },
        {
          authority: "ram",
          controlNo: "",
          heading: "Joruba (taal)",
        },
        {
          authority: "",
          controlNo: "",
          heading: "Yoruba (langue)",
        },
        {
          authority: "gtt",
          controlNo: "",
          heading: "Yoruba language",
        },
        {
          authority: "gtt",
          controlNo: "",
          heading: "more subjects",
        },
        {
          authority: "fast",
          controlNo: "(OCoLC)fst01423865",
          heading: "Textbooks",
        },
        {
          authority: "gtt",
          controlNo: "(NL-LeOCL)138474974",
          heading: "Texts (form)",
        },
        {
          authority: "fast",
          controlNo: "(OCoLC)fst01423896",
          heading: "Readers",
        },
      ],
      title: "Yoruba; intermediate texts",
      uuid: "15156b66-fe7d-4d83-b96b-c96e25a39338",
    },
    responseType: "singleWork",
    status: 200,
    timestamp: "Wed, 14 Apr 2021 21:38:15 GMT",
  };
};

export const workDetail = createWorkResult();
const inCollections = [
  {
    creator: "Placeholder creator",
    description: "Placeholder description",
    numberOfItems: 3,
    title: "Placeholder title",
    uuid: "37a7e91d-31cd-444c-8e97-7f17426de7ec",
  },
];
export const workDetailInCollection = createWorkResult(inCollections);

const defaultWorkDetailData = {
  alt_titles: [],
  authors: [],
  contributors: [],
  dates: null,
  edition_count: 1,
  editions: [
    {
      edition: null,
      edition_id: 4292508,
      edition_statement: null,
      extent: "1 v. (53 p.)",
      items: [
        {
          content_type: "ebook",
          contributors: [],
          drm: null,
          item_id: 4943167,
          links: [
            {
              flags: {
                catalog: true,
                download: false,
                reader: false,
              },
              link_id: 6113936,
              mediaType: "text/html",
              url: "www.nypl.org/research/collections/shared-collection-catalog/bib/b15804181",
            },
          ],
          location: null,
          measurements: null,
          modified: null,
          rights: [],
          source: "nypl",
        },
      ],
      languages: [
        {
          iso_2: "en",
          iso_3: "eng",
          language: "English",
        },
      ],
      links: [],
      publication_date: "1650",
      publication_place: "New York (State)",
      publishers: [],
      summary:
        '{"Testimony against Hugh Parsons, taken before Judge William Pynchon at Springfield, Massachusetts. "}',
      table_of_contents: null,
      title: "Testimony against Hugh Parsons charged with witchcraft,",
      volume: null,
      work_uuid: "38fd9f4c-23f3-4642-b449-d3478b12f1e2",
    },
  ],
  inCollections: [],
  languages: [
    {
      iso_2: "en",
      iso_3: "eng",
      language: "English",
    },
  ],
  measurements: [],
  medium: null,
  series: null,
  series_position: null,
  sub_title: null,
  subjects: [
    {
      authority: "lcsh",
      controlNo: "",
      heading: "Trials (Witchcraft) -- Springfield",
    },
  ],
  title: "Testimony against Hugh Parsons charged with witchcraft,",
  uuid: "38fd9f4c-23f3-4642-b449-d3478b12f1e2",
};
export const workDetailWithCatalog: WorkResult = {
  data: defaultWorkDetailData,
  responseType: "singleWork",
  status: 200,
  timestamp: "Wed, 09 Mar 2022 22:09:52 GMT",
};

export const workDetailWithUp: WorkResult = {
  data: {
    ...defaultWorkDetailData,
    editions: [
      {
        items: [
          {
            links: [
              {
                url: "test-link-url",
                link_id: 12,
                mediaType: "application/epub+xml",
                flags: {
                  catalog: false,
                  download: false,
                  fulfill_limited_access: true,
                  reader: true,
                },
              },
              {
                url: "https://backend.msw/fulfill/12345",
                link_id: 12345,
                mediaType: "application/epub+zip",
                flags: {
                  catalog: false,
                  download: true,
                  reader: false,
                  nypl_login: true,
                },
              },
            ],
          },
        ],
        title: "title",
      },
    ],
    title: "title",
  },
  responseType: "singleWork",
  status: 200,
  timestamp: "Wed, 09 Mar 2022 22:09:52 GMT",
};

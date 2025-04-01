import { EditionResult } from "~/src/types/EditionQuery";
import { OpdsMetadata } from "~/src/types/OpdsModel";

const createEditionResult = (
  inCollections: OpdsMetadata[] = []
): EditionResult => {
  return {
    data: {
      edition: null,
      edition_id: 1780467,
      edition_statement: "Placeholder edition statement",
      extent: "1 online resource.",
      inCollections: inCollections,
      instances: [
        {
          authors: [
            {
              lcnaf: "true",
              name: "Edgar, John. ()",
              viaf: "",
            },
          ],
          contributors: [],
          dates: [
            {
              date: "[ca. 1923]",
              type: "publication_date",
            },
          ],
          extent: "239 Seiten",
          identifiers: [
            {
              authority: "oclc",
              identifier: "917807850",
            },
            {
              authority: "owi",
              identifier: "7183098",
            },
          ],
          instance_id: 40727132,
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
              item_id: 2178893,
              links: [
                {
                  link_id: 3667191,
                  mediaType: "application/pdf",
                  url: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=mdp.39015002660481",
                  flags: {
                    catalog: false,
                    download: true,
                    reader: false,
                    embed: false,
                  },
                },
                {
                  link_id: 3667190,
                  mediaType: "text/html",
                  url: "babel.hathitrust.org/cgi/pt?id=mdp.39015002660481",
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
          languages: null,
          publication_place: "Paris, France",
          publishers: [
            {
              lcnaf: "",
              name: "Miller,",
              viaf: "",
            },
          ],
          summary: null,
          table_of_contents: null,
          title:
            "A history of South Africa from the earliest European settlement / ",
        },
        {
          authors: [
            {
              lcnaf: "true",
              name: "Edgar, John. ()",
              viaf: "",
            },
          ],
          contributors: [],
          dates: [
            {
              date: "2000",
              type: "publication_date",
            },
          ],
          extent: "239 Seiten",
          identifiers: [
            {
              authority: "oclc",
              identifier: "917807850",
            },
            {
              authority: "owi",
              identifier: "7183098",
            },
          ],
          instance_id: 40727150,
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
              item_id: 1234567,
              links: [
                {
                  link_id: 3667191,
                  mediaType: "application/pdf",
                  url: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=mdp.39015002660481",
                  flags: {
                    catalog: false,
                    download: true,
                    reader: false,
                    embed: false,
                  },
                },
                {
                  link_id: 3667190,
                  mediaType: "text/html",
                  url: "babel.hathitrust.org/cgi/pt?id=mdp.39015002660481",
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
          languages: null,
          publication_place: "Paris, France",
          publishers: [
            {
              lcnaf: "",
              name: "Publisher 1",
              viaf: "",
            },
          ],
          summary: null,
          table_of_contents: null,
          title:
            "A history of South Africa from the earliest European settlement / ",
        },
      ],
      languages: [
        {
          iso_2: "",
          iso_3: "eng",
          language: "French",
        },
        {
          iso_2: "",
          iso_3: "eng",
          language: "Undetermined",
        },
      ],
      publication_date: "1923",
      publication_place: "Paris",
      publishers: [
        {
          lcnaf: "",
          name: "T. Maskew Miller; B. Blackwell ltd.",
          viaf: "",
        },
        {
          lcnaf: "",
          name: "Miller,",
          viaf: "",
        },
      ],
      sub_title: "sub title",
      summary: "Placeholder Summary",
      table_of_contents:
        "La marchandisation des services d'eau : les réformes des années 1980-1990. La fragmentation par les réseaux. Géographie des nouveaux assemblages en Afrique subsaharienne. Le pluralisme sans l'équité? L'écartèlement des territoires nationaux. Spatialisation et territorialisation des services d'eau : une inégale fragmentation.",
      title: "A history of South Africa from the earliest European settlement",
      volume: "Volume number",
      work_authors: [
        {
          lcnaf: "",
          name: "Edgar, John, 1876-",
          primary: "true",
          viaf: "",
        },
        {
          lcnaf: "n78095332",
          name: "Shakespeare, William- ()",
          primary: "true",
          viaf: "96994048",
        },
      ],
      work_uuid: "0007511d-29be-4a3c-9965-fe367c55b1f8",
      work_title:
        "A history of South Africa from the earliest European settlement",
    },
    responseType: "singleEdition",
    status: 200,
    timestamp: "Thu, 15 Apr 2021 22:32:55 GMT",
  };
};

export const editionDetail = createEditionResult();
const inCollections = [
  {
    creator: "Placeholder creator",
    description: "Placeholder description",
    numberOfItems: 3,
    title: "Placeholder title",
    uuid: "37a7e91d-31cd-444c-8e97-7f17426de7ec",
  },
];
export const editionDetailInCollection = createEditionResult(inCollections);

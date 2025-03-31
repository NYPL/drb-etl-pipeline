import { ApiSearchResult } from "~/src/types/SearchQuery";

export const searchResults: ApiSearchResult = {
  data: {
    facets: {
      formats: [
        {
          count: 6,
          value: "text/html",
        },
        {
          count: 6,
          value: "application/pdf",
        },
      ],
      languages: [
        {
          count: 6,
          value: "English",
        },
      ],
    },
    paging: {
      currentPage: 1,
      firstPage: 1,
      lastPage: 3,
      nextPage: 2,
      previousPage: null,
      recordsPerPage: 10,
    },
    totalWorks: 26,
    works: [
      {
        alt_titles: ["Lungs of the alligator"],
        authors: [
          {
            lcnaf: "",
            name: "Nook, Tammy",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Timmy",
            primary: "true",
            viaf: "",
          },
        ],
        contributors: [],
        dates: null,
        edition_count: 3,
        editions: [
          {
            edition: null,
            edition_id: 1453292,
            edition_statement: null,
            extent: null,
            items: [
              {
                content_type: "ebook",
                contributors: [
                  {
                    lcnaf: "",
                    name: "University of Illinois at Urbana-Champaign",
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
                item_id: 1956736,
                links: [
                  {
                    link_id: 3330416,
                    mediaType: "text/html",
                    url: "test-link-url-2",
                    flags: {
                      catalog: false,
                      download: false,
                      reader: false,
                      embed: true,
                    },
                  },
                  {
                    link_id: 3330415,
                    mediaType: "application/pdf",
                    url: "test-link-url-3",
                    flags: {
                      catalog: false,
                      download: true,
                      reader: false,
                    },
                  },
                ],
                location: null,
                measurements: null,
                modified: null,
                rights: [
                  {
                    license: "public_domain",
                    rightsStatement: "Public Domain",
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
              {
                iso_2: "es",
                iso_3: "esp",
                language: "Spanish",
              },
            ],
            links: [
              {
                link_id: 1614426,
                mediaType: "image/jpeg",
                url: "test-cover-2",
                flags: {
                  catalog: false,
                  download: false,
                  reader: false,
                },
              },
            ],
            publication_date: "1915",
            publication_place: "Island Getaway",
            publishers: [
              {
                lcnaf: "",
                name: "Nook Industries",
                viaf: "",
              },
            ],
            summary: null,
            table_of_contents: null,
            title: "Alligator book",
            volume: null,
            work_uuid: "15a4aeb9-e9fb-43d8-b7f0-4e4a43e415ef",
          },
        ],
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
        sub_title: "Cute Tables Subtitle",
        subjects: [
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00805630",
            heading: "Embryology",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00908425",
            heading: "Alligators",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00805630",
            heading: "American alligator",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst01003744",
            heading: "Lungs",
          },
        ],
        title: "Happy Home Companion: Cute Tables",
        uuid: "test-uuid-1",
      },
      {
        alt_titles: [],
        authors: [
          {
            lcnaf: "",
            name: "display author",
            primary: "",
            viaf: "12345",
          },
        ],
        contributors: [],
        dates: null,
        edition_count: 1,
        editions: [
          {
            edition: null,
            edition_id: 1172733,
            edition_statement: null,
            extent: null,
            items: [
              {
                content_type: "ebook",
                contributors: null,
                drm: null,
                item_id: 1579612,
                links: null,
                location: null,
                measurements: null,
                modified: null,
                rights: null,
                source: "hathitrust",
              },
            ],
            languages: null,
            links: [],
            publication_date: null,
            publication_place: null,
            publishers: [],
            summary: null,
            table_of_contents: null,
            title:
              "The alligator and its allies, by Albert M. Reese ... with 62 figures and 28 plates",
            volume: null,
            work_uuid: "99ca3bdd-72c5-4a71-8446-c963f985bd04",
          },
        ],
        languages: [],
        measurements: [],
        medium: null,
        series: null,
        series_position: null,
        sub_title: null,
        subjects: [],
        title:
          "The alligator and its allies, by Albert M. Reese ... with 62 figures and 28 plates",
        uuid: "test-uuid-2",
      },
      {
        alt_titles: ["Lungs of the alligator"],
        authors: [
          {
            lcnaf: "",
            name: "Nook, Tom",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom1",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom2",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom3",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom4",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom5",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom6",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom7",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom8",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom9",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom10",
            primary: "",
            viaf: "",
          },
          {
            lcnaf: "",
            name: "Nook, Tom11",
            primary: "",
            viaf: "",
          },
        ],
        contributors: [],
        dates: null,
        edition_count: 5,
        editions: [
          {
            edition: null,
            edition_id: 1453292,
            edition_statement: null,
            extent: null,
            items: [
              {
                content_type: "ebook",
                contributors: [
                  {
                    lcnaf: "",
                    name: "University of Illinois at Urbana-Champaign",
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
                item_id: 1956736,
                links: [
                  {
                    link_id: 3234,
                    mediaType: "text/html",
                    url: "test-link-url-5",
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
                    license: "public_domain",
                    rightsStatement:
                      "Public Domain Public Domain Public Domain Public Domain Public Domain Public Domain Public Domain Public Domain Public Domain",
                    source: "hathitrust",
                  },
                  {
                    license: "public_domain",
                    rightsStatement: "Public Domain 2",
                    source: "hathitrust",
                  },
                  {
                    license: "public_domain",
                    rightsStatement: "Public Domain 3",
                    source: "hathitrust",
                  },
                ],
                source: "hathitrust",
              },
              {
                content_type: "ebook",
                contributors: [
                  {
                    lcnaf: "",
                    name: "University of Illinois at Urbana-Champaign",
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
                item_id: 1956736,
                links: [
                  {
                    link_id: 3330415,
                    mediaType: "application/pdf",
                    url: "test-link-url-4",
                    flags: {
                      catalog: false,
                      download: true,
                      reader: false,
                      embed: false,
                    },
                  },
                ],
                location: null,
                measurements: null,
                modified: null,
                rights: [
                  {
                    license: "public_domain",
                    rightsStatement: "Public Domain 2",
                    source: "hathitrust",
                  },
                  {
                    license: "public_domain",
                    rightsStatement: "Public Domain 3",
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
                language: "Lang1",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang2",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang3",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang4",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang5",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang6",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang7",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang8",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang9",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang10",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang11",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang12",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang13",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang14",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang15",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang16",
              },
              {
                iso_2: "sv",
                iso_3: "swe",
                language: "Lang17",
              },
            ],
            links: [
              {
                link_id: 1614426,
                mediaType: "image/jpeg",
                url: "test-cover-2",
                flags: {
                  catalog: false,
                  download: false,
                  reader: false,
                },
              },
            ],
            publication_date: "1945",
            publication_place:
              "Taumatawhakatangihangakoauauotamateaturipukakapikimaungahoronukupokaiwhenuakitanatahu",
            publishers: [
              {
                lcnaf: "",
                name: "Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries Nook Industries ",
                viaf: "",
              },
              {
                lcnaf: "",
                name: "Nook Industries 2",
                viaf: "",
              },
              {
                lcnaf: "",
                name: "Nook Industries 3",
                viaf: "",
              },
              {
                lcnaf: "",
                name: "Nook Industries 4",
                viaf: "",
              },
              {
                lcnaf: "",
                name: "Nook Industries 5",
                viaf: "",
              },
            ],
            summary: null,
            table_of_contents: null,
            title: "Alligator book",
            volume: null,
            work_uuid: "15a4aeb9-e9fb-43d8-b7f0-4e4a43e415ef",
          },
        ],
        languages: [
          {
            iso_2: "en",
            iso_3: "eng",
            language: "English",
          },
          {
            iso_2: "es",
            iso_3: "esp",
            language: "Spanish",
          },
        ],
        measurements: [],
        medium: null,
        series: null,
        series_position: null,
        sub_title:
          "super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long super long  Subtitle",
        subjects: [
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00805630",
            heading: "Embryology",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00908425",
            heading: "Alligators",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst00805630",
            heading: "American alligator",
          },
          {
            authority: "fast",
            controlNo: "(OCoLC)fst01003744",
            heading: "Lungs",
          },
        ],
        title:
          "Happy Home Companion: super super super supersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersupersuper long title",
        uuid: "test-uuid-3",
      },
    ],
  },
  responseType: "searchResponse",
  status: 200,
  timestamp: "Wed, 14 Apr 2021 17:12:23 GMT",
};

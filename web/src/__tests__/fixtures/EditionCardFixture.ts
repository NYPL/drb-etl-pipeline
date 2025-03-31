import { WorkEdition } from "~/src/types/DataModel";

export const fullEdition: WorkEdition = {
  edition_id: 12345,
  publication_place: "Chargoggagoggmanchauggagoggchaubunagungamaugg",
  publication_date: "1990",
  links: [
    {
      link_id: 32,
      url: "test-cover",
      mediaType: "image/jpeg",
      flags: {
        catalog: false,
        download: false,
        reader: false,
      },
    },
    {
      link_id: 33,
      url: "test-cover-2",
      mediaType: "image/jpeg",
      flags: {
        catalog: false,
        download: false,
        reader: false,
      },
    },
  ],
  publishers: [{ name: "publisher_1", roles: ["publisher"] }],
  languages: [
    { language: "english" },
    { language: "french" },
    { language: "russian" },
    { language: "unknown" },
    { language: "spanish" },
    { language: "german" },
    { language: "arabic" },
    { language: "hindi" },
    { language: "japanese" },
    { language: "vietnamese" },
    { language: "latin" },
    { language: "romanian" },
  ],
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
            reader: true,
          },
        },
        {
          url: "test-link-url-2",
          link_id: 23,
          mediaType: "application/epub+zip",
          flags: {
            catalog: false,
            download: true,
            reader: false,
          },
        },
        {
          url: "test-link-url-3",
          link_id: 34,
          mediaType: "application/html+edd",
          flags: {
            catalog: false,
            download: false,
            reader: false,
            edd: true,
          },
        },
      ],
      rights: [
        {
          license: "license content",
          rightsStatement: "test rights statement",
        },
      ],
    },
  ],
};

export const eddEdition: WorkEdition = {
  ...fullEdition,
  items: [
    {
      links: [
        {
          url: "test-link-url",
          link_id: 1,
          mediaType: "application/html+edd",
          flags: {
            catalog: false,
            download: false,
            reader: false,
            edd: true,
          },
        },
      ],
    },
  ],
};

export const upEdition: WorkEdition = {
  ...fullEdition,
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
            reader: true,
            nypl_login: true,
          },
        },
        {
          url: "test-link-url-2",
          link_id: 23,
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
};

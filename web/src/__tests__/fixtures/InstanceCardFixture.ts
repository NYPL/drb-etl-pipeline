import { Instance } from "~/src/types/DataModel";

export const fullInstance: Instance = {
  instance_id: 12345,
  publishers: [{ name: "publisher_1", roles: ["publisher"] }],
  publication_place: "Paris",
  title: "title",
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
  identifiers: [
    {
      authority: "ddc",
      identifier: "300",
    },
    {
      authority: "oclc",
      identifier: "1014189544",
    },
    {
      authority: "oclc",
      identifier: "1030816762",
    },
  ],
};

export const eddInstance: Instance = {
  ...fullInstance,
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

export const upInstance: Instance = {
  ...fullInstance,
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

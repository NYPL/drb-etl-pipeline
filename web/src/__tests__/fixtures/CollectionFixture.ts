import { CollectionResult } from "~/src/types/CollectionQuery";
import { Opds2Feed, OpdsPublication } from "~/src/types/OpdsModel";

export const collections = [
  {
    title: "Baseball: A Collection by Mike Benowitz",
    href: "/collection/978ea0e0-8ecc-4de2-bfe8-032fea641d8e",
  },
  {
    title: "Error Test Collection 1",
    href: "/collection/42ba2f91-6802-45e2-8863-7afafec8cc2c",
  },
  {
    title: "Error Test Collection 2",
    href: "/collection/d292ac5b-18dd-472f-a422-9d32cfa33659",
  },
  {
    title: "Historical Resources on Marblehead 1",
    href: "/collection/0104a1ec-8e03-4ee8-9149-92516c119b40",
  },
  {
    title: "Historical Resources on Marblehead 2",
    href: "/collection/b1e7f7d4-6822-4cc6-a82b-ee111252ac08",
  },
  {
    title: "Historical Resources on Marblehead 3",
    href: "/collection/d505f3b3-8efa-49cb-b478-309ab629128e",
  },
  {
    title: "Historical Resources on Marblehead 4",
    href: "/collection/53307b1c-64a1-449f-967c-f6d84d952e85",
  },
  {
    title: "Historical Resources on Marblehead 5",
    href: "/collection/8cf9a31e-3097-458c-84c9-5fb1b1cac25b",
  },
];

export const oneCollectionListData: Opds2Feed = {
  groups: [
    {
      links: [
        {
          href: "/collection/978ea0e0-8ecc-4de2-bfe8-032fea641d8e?page=1",
          rel: ["self", "first", "previous", "next", "last"],
          type: "application/opds+json",
        },
      ],
      metadata: {
        creator: "Mike Benowitz",
        currentPage: 1,
        description: "A history of the sport of baseball",
        itemsPerPage: 5,
        numberOfItems: 3,
        title: "Baseball: A Collection by Mike Benowitz",
      },
      publications: [
        {
          editions: [],
          images: [
            {
              href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
              type: "image/png",
            },
          ],
          links: [
            {
              href: "www.nypl.org/research/collections/shared-collection-catalog/bib/b14514889",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "application/html+catalog",
            },
            {
              href: "www.nypl.org/research/collections/shared-collection-catalog/hold/request/b14514889-i38116343",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "application/html+edd",
            },
            {
              href: "https://drb-qa.nypl.org/edition/4267756",
              rel: "alternate",
              type: "text/html",
            },
          ],
          metadata: {
            alternate: [],
            created: "Tue, 18 May 2021 10:00:41 GMT",
            creator: "Wray, J. E. (J. Edward)",
            description: '{"Master microform held by: NN."}',
            language: "eng",
            locationCreated: "New York (State)",
            modified: "Tue, 18 May 2021 10:00:41 GMT",
            published: 1900,
            publisher: "American Sports Publishing,",
            sortAs:
              "how to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
            subtitle: null,
            title:
              "How to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
          },
          type: "application/opds-publication+json",
        },
        {
          editions: [],
          images: [
            {
              href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
              type: "image/png",
            },
          ],
          links: [
            {
              href: "catalog.hathitrust.org/api/volumes/oclc/67612618.html",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "text/html",
            },
            {
              href: "https://drb-qa.nypl.org/edition/2422118",
              rel: "alternate",
              type: "text/html",
            },
          ],
          metadata: {
            ["@type"]: "http://schema.org/Book",
            alternate: [],
            created: "Thu, 22 Apr 2021 10:00:39 GMT",
            creator: " Committee on Energy and Natural Resources.",
            description: null,
            language: "eng",
            locationCreated: null,
            modified: "Thu, 22 Apr 2021 10:00:39 GMT",
            published: 2006,
            publisher: "[U.S. G.P.O.],",
            sortAs: "negro leagues baseball museum",
            subtitle: null,
            title: "Negro Leagues Baseball Museum",
          },
          type: "application/opds-publication+json",
        },
        {
          editions: [],
          images: [
            {
              href: "drb-files-qa.s3.amazonaws.com/covers/hathi/mdp.39015047482628.jpeg",
              type: "image/jpeg",
            },
          ],
          links: [
            {
              href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047482628",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "text/html",
            },
            {
              href: "catalog.hathitrust.org/api/volumes/oclc/275274.html",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "text/html",
            },
            {
              href: "catalog.hathitrust.org/api/volumes/oclc/2192781.html",
              rel: "http://opds-spec.org/acquisition/open-access",
              type: "text/html",
            },
            {
              href: "https://drb-qa.nypl.org/edition/894734",
              rel: "alternate",
              type: "text/html",
            },
          ],
          metadata: {
            "@type": "http://schema.org/Book",
            alternate: [],
            created: "Tue, 30 Mar 2021 19:29:20 GMT",
            creator: "Spink, J. G. Taylor b. 1888.",
            description: null,
            language: "eng,und",
            locationCreated: null,
            modified: "Tue, 30 Mar 2021 19:29:20 GMT",
            published: 1947,
            publisher:
              "Thomas Y. Crowell,, T. Y. Crowell Co., Crowell, New York",
            sortAs: "judge landis and twenty-five years of baseball",
            subtitle: null,
            title: "Judge Landis and twenty-five years of baseball",
          },
          type: "application/opds-publication+json",
        },
      ],
    },
  ],
  links: [
    {
      href: "/collections?page=1",
      rel: ["self", "first", "previous", "next", "last"],
      type: "application/opds+json",
    },
  ],
  metadata: {
    currentPage: 1,
    itemsPerPage: 10,
    numberOfItems: 1,
    title: "Digital Research Books Collections",
  },
};

export const collectionListData: CollectionResult = {
  collections: {
    groups: [
      {
        links: [
          {
            href: "/collection/978ea0e0-8ecc-4de2-bfe8-032fea641d8e?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A history of the sport of baseball",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Baseball: A Collection by Mike Benowitz",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "www.nypl.org/research/collections/shared-collection-catalog/bib/b14514889",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/html+catalog",
              },
              {
                href: "www.nypl.org/research/collections/shared-collection-catalog/hold/request/b14514889-i38116343",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/html+edd",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4267756",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              alternate: [],
              created: "Tue, 18 May 2021 10:00:41 GMT",
              creator: "Wray, J. E. (J. Edward)",
              description: '{"Master microform held by: NN."}',
              language: "eng",
              locationCreated: "New York (State)",
              modified: "Tue, 18 May 2021 10:00:41 GMT",
              published: 1900,
              publisher: "American Sports Publishing,",
              sortAs:
                "how to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
              subtitle: null,
              title:
                "How to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/67612618.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/2422118",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              ["@type"]: "http://schema.org/Book",
              alternate: [],
              created: "Thu, 22 Apr 2021 10:00:39 GMT",
              creator: " Committee on Energy and Natural Resources.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Thu, 22 Apr 2021 10:00:39 GMT",
              published: 2006,
              publisher: "[U.S. G.P.O.],",
              sortAs: "negro leagues baseball museum",
              subtitle: null,
              title: "Negro Leagues Baseball Museum",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "drb-files-qa.s3.amazonaws.com/covers/hathi/mdp.39015047482628.jpeg",
                type: "image/jpeg",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047482628",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/275274.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/2192781.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/894734",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Tue, 30 Mar 2021 19:29:20 GMT",
              creator: "Spink, J. G. Taylor b. 1888.",
              description: null,
              language: "eng,und",
              locationCreated: null,
              modified: "Tue, 30 Mar 2021 19:29:20 GMT",
              published: 1947,
              publisher:
                "Thomas Y. Crowell,, T. Y. Crowell Co., Crowell, New York",
              sortAs: "judge landis and twenty-five years of baseball",
              subtitle: null,
              title: "Judge Landis and twenty-five years of baseball",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/42ba2f91-6802-45e2-8863-7afafec8cc2c?page=1",
            rel: ["self", "first", "previous"],
            type: "application/opds+json",
          },
          {
            href: "/collection/42ba2f91-6802-45e2-8863-7afafec8cc2c?page=0",
            rel: ["next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "Testing Sean's error report",
          itemsPerPage: 5,
          numberOfItems: 0,
          title: "Error Test Collection 1",
        },
      },
      {
        links: [
          {
            href: "/collection/d292ac5b-18dd-472f-a422-9d32cfa33659?page=1",
            rel: ["self", "first", "previous"],
            type: "application/opds+json",
          },
          {
            href: "/collection/d292ac5b-18dd-472f-a422-9d32cfa33659?page=0",
            rel: ["next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "Testing Sean's error report",
          itemsPerPage: 5,
          numberOfItems: 0,
          title: "Error Test Collection 2",
        },
      },
      {
        links: [
          {
            href: "/collection/0104a1ec-8e03-4ee8-9149-92516c119b40?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 1",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/b1e7f7d4-6822-4cc6-a82b-ee111252ac08?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 2",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/d505f3b3-8efa-49cb-b478-309ab629128e?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 3",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/53307b1c-64a1-449f-967c-f6d84d952e85?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 4",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/8cf9a31e-3097-458c-84c9-5fb1b1cac25b?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 5",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/d902fd44-7cbe-4401-b50c-5b1bda8b1059?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 6",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
      {
        links: [
          {
            href: "/collection/37a7e91d-31cd-444c-8e97-7f17426de7ec?page=1",
            rel: ["self", "first", "previous", "next", "last"],
            type: "application/opds+json",
          },
        ],
        metadata: {
          creator: "Mike Benowitz",
          currentPage: 1,
          description: "A town in Massachussetts",
          itemsPerPage: 5,
          numberOfItems: 3,
          title: "Historical Resources on Marblehead 7",
        },
        publications: [
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=coo1.ark:/13960/t2t448c98",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=wu.89077236636",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829537",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/3486873.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662693",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, (1853-1904.)",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1880,
              publisher: "Houghton, Osgood",
              sortAs:
                "the history and traditions of marblehead. by samuel roads",
              subtitle: null,
              title:
                "The history and traditions of Marblehead. By Samuel Roads",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t08w3k590",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/imgsrv/download/pdf?id=loc.ark:/13960/t3417498d",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "application/pdf",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047402535",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=hvd.32044013685672",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081829529",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/1273431",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Sun, 04 Apr 2021 10:00:40 GMT",
              creator: "Marblehead historical society.",
              description: null,
              language: "eng",
              locationCreated: "Massachusetts",
              modified: "Sun, 04 Apr 2021 10:00:40 GMT",
              published: 1915,
              publisher: "",
              sortAs:
                "old marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the marblehead historical society by benjamin j. lindsey, treasurer",
              subtitle: null,
              title:
                "Old Marblehead sea captains and the ships in which they sailed ... comp. and pub. for the benefit of the Marblehead historical society by Benjamin J. Lindsey, treasurer",
            },
            type: "application/opds-publication+json",
          },
          {
            editions: [],
            images: [
              {
                href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
                type: "image/png",
              },
            ],
            links: [
              {
                href: "babel.hathitrust.org/cgi/pt?id=nyp.33433081828323",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "catalog.hathitrust.org/api/volumes/oclc/35897189.html",
                rel: "http://opds-spec.org/acquisition/open-access",
                type: "text/html",
              },
              {
                href: "https://drb-qa.nypl.org/edition/4662646",
                rel: "alternate",
                type: "text/html",
              },
            ],
            metadata: {
              "@type": "http://schema.org/Book",
              alternate: [],
              created: "Fri, 04 Jun 2021 10:00:41 GMT",
              creator: "Roads, Samuel, Jr.",
              description: null,
              language: "eng",
              locationCreated: null,
              modified: "Fri, 04 Jun 2021 10:00:41 GMT",
              published: 1881,
              publisher: "M.H. Graves [cop, Merrill H. Graves,, C.H. Litchman,",
              sortAs: "a guide to marblehead",
              subtitle: null,
              title: "A guide to Marblehead",
            },
            type: "application/opds-publication+json",
          },
        ],
      },
    ],
    links: [
      {
        href: "/collections?page=1",
        rel: ["self", "first", "previous", "next", "last"],
        type: "application/opds+json",
      },
    ],
    metadata: {
      currentPage: 1,
      itemsPerPage: 10,
      numberOfItems: 10,
      title: "Digital Research Books Collections",
    },
  },
};

const defaultPublications: OpdsPublication[] = [
  {
    editions: [],
    images: [
      {
        href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
        type: "image/png",
      },
    ],
    links: [
      {
        href: "www.nypl.org/research/collections/shared-collection-catalog/bib/b14514889",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "application/html+catalog",
      },
      {
        href: "www.nypl.org/research/collections/shared-collection-catalog/hold/request/b14514889-i38116343",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "application/html+edd",
      },
      {
        href: "https://drb-qa.nypl.org/edition/4267756",
        rel: "alternate",
        type: "text/html",
      },
    ],
    metadata: {
      alternate: [],
      created: "Tue, 18 May 2021 10:00:41 GMT",
      creator: "Wray, J. E. (J. Edward)",
      description: '{"Master microform held by: NN."}',
      language: "eng",
      locationCreated: "New York (State)",
      modified: "Tue, 18 May 2021 10:00:41 GMT",
      published: 1900,
      publisher: "American Sports Publishing,",
      sortAs:
        "how to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
      subtitle: null,
      title:
        "How to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
    },
    type: "application/opds-publication+json",
  },
  {
    editions: [],
    images: [
      {
        href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
        type: "image/png",
      },
    ],
    links: [
      {
        href: "catalog.hathitrust.org/api/volumes/oclc/67612618.html",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "text/html",
      },
      {
        href: "https://drb-qa.nypl.org/edition/2422118",
        rel: "alternate",
        type: "text/html",
      },
    ],
    metadata: {
      ["@type"]: "http://schema.org/Book",
      alternate: [],
      created: "Thu, 22 Apr 2021 10:00:39 GMT",
      creator: " Committee on Energy and Natural Resources.",
      description: null,
      language: "eng",
      locationCreated: null,
      modified: "Thu, 22 Apr 2021 10:00:39 GMT",
      published: 2006,
      publisher: "[U.S. G.P.O.],",
      sortAs: "negro leagues baseball museum",
      subtitle: null,
      title: "Negro Leagues Baseball Museum",
    },
    type: "application/opds-publication+json",
  },
  {
    editions: [],
    images: [
      {
        href: "drb-files-qa.s3.amazonaws.com/covers/hathi/mdp.39015047482628.jpeg",
        type: "image/jpeg",
      },
    ],
    links: [
      {
        href: "babel.hathitrust.org/cgi/pt?id=mdp.39015047482628",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "text/html",
      },
      {
        href: "catalog.hathitrust.org/api/volumes/oclc/275274.html",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "text/html",
      },
      {
        href: "catalog.hathitrust.org/api/volumes/oclc/2192781.html",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "text/html",
      },
      {
        href: "https://drb-qa.nypl.org/edition/894734",
        rel: "alternate",
        type: "text/html",
      },
    ],
    metadata: {
      "@type": "http://schema.org/Book",
      alternate: [],
      created: "Tue, 30 Mar 2021 19:29:20 GMT",
      creator: "Spink, J. G. Taylor b. 1888.",
      description: null,
      language: "eng,und",
      locationCreated: null,
      modified: "Tue, 30 Mar 2021 19:29:20 GMT",
      published: 1947,
      publisher: "Thomas Y. Crowell,, T. Y. Crowell Co., Crowell, New York",
      sortAs: "judge landis and twenty-five years of baseball",
      rights: {
        license: "public_domain",
        rightsStatement: "Public Domain",
        source: "hathitrust",
      },
      subtitle: null,
      title: "Judge Landis and twenty-five years of baseball",
    },
    type: "application/opds-publication+json",
  },
];

const createCollectionItem = (title = "Default title"): OpdsPublication => {
  return {
    editions: [],
    images: [
      {
        href: "https://drb-files-qa.s3.amazonaws.com/covers/default/defaultCover.png",
        type: "image/png",
      },
    ],
    links: [
      {
        href: "www.nypl.org/research/collections/shared-collection-catalog/bib/b14514889",
        identifier: "catalog",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "application/html+catalog",
      },
      {
        href: "www.nypl.org/research/collections/shared-collection-catalog/hold/request/b14514889-i38116343",
        identifier: "requestable",
        rel: "http://opds-spec.org/acquisition/open-access",
        type: "application/html+edd",
      },
      {
        href: "https://drb-qa.nypl.org/edition/4267756",
        identifier: "readable",
        rel: "alternate",
        type: "text/html",
      },
    ],
    metadata: {
      "@type": "http://schema.org/Book",
      alternate: [],
      created: "Tue, 18 May 2021 10:00:41 GMT",
      creator: "Wray, J. E. (J. Edward)",
      description: '{"Master microform held by: NN."}',
      language: "eng",
      locationCreated: "New York (State)",
      modified: "Tue, 18 May 2021 10:00:41 GMT",
      published: 1900,
      publisher: "American Sports Publishing,",
      sortAs:
        "how to organize a league, manage a team, captain a team, coach a team, score a game, arrange signals [microform] including how to lay out a league diamond, and technical terms of base ball,",
      subtitle: null,
      title: title,
    },
    type: "application/opds-publication+json",
  };
};

const createCollectionData = (
  publications = defaultPublications
): CollectionResult => {
  return {
    collections: {
      links: [
        {
          href: "/collection/978ea0e0-8ecc-4de2-bfe8-032fea641d8e?page=1",
          rel: ["self", "first", "previous", "next", "last"],
          type: "application/opds+json",
        },
      ],
      metadata: {
        creator: "Mike Benowitz",
        currentPage: 1,
        description: "A history of the sport of baseball",
        itemsPerPage: 5,
        numberOfItems: publications.length,
        title: "Baseball: A Collection by Mike Benowitz",
      },
      publications: publications,
    },
  };
};

const createPaginationData = () => {
  const publications: OpdsPublication[] = [];
  for (let i = 0; i < 20; ++i) {
    publications.push(createCollectionItem(`Title ${i}`));
  }
  return createCollectionData(publications);
};

export const collectionItem: OpdsPublication = createCollectionItem();
export const collectionData: CollectionResult = createCollectionData();
export const collectionWithPagination: CollectionResult =
  createPaginationData();
export const emptyCollectionResult: CollectionResult = createCollectionData([]);

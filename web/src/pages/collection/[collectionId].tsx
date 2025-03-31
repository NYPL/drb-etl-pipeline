import { GetServerSideProps } from "next";
import Head from "next/head";
import React from "react";
import Collection from "~/src/components/Collection/Collection";

import Layout from "~/src/components/Layout/Layout";
import { MAX_PAGE_TITLE_LENGTH } from "~/src/constants/editioncard";
import { documentTitles } from "~/src/constants/labels";
import { collectionFetcher } from "~/src/lib/api/CollectionApi";
import { CollectionQuery, CollectionResult } from "~/src/types/CollectionQuery";
import { truncateStringOnWhitespace } from "~/src/util/Util";
import Error from "../_error";

export const getServerSideProps: GetServerSideProps = async (context) => {
  const collectionQuery: CollectionQuery = {
    identifier: String(context.query.collectionId),
    page: context.query.page ? Number(context.query.page) : 1,
    perPage: context.query.perPage ? Number(context.query.perPage) : 10,
    sort: context.query.sort ? String(context.query.sort) : "relevance",
  };

  const collectionResult: CollectionResult = await collectionFetcher(
    collectionQuery
  );
  return {
    props: {
      collectionResult: collectionResult,
      collectionQuery: collectionQuery,
    },
  };
};

const CollectionResults: React.FC<{
  collectionResult: CollectionResult;
  collectionQuery: CollectionQuery;
}> = ({ collectionResult, collectionQuery }) => {
  if (collectionResult.statusCode) {
    return <Error statusCode={collectionResult.statusCode} />;
  }

  return (
    <Layout>
      <Head>
        <title>
          {`${truncateStringOnWhitespace(
            collectionResult.collections.metadata.title,
            MAX_PAGE_TITLE_LENGTH
          )} | ${documentTitles.collection}`}
        </title>
      </Head>
      <Collection
        collectionResult={collectionResult}
        collectionQuery={collectionQuery}
      />
    </Layout>
  );
};

export default CollectionResults;

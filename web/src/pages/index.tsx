import React from "react";

import Layout from "~/src/components/Layout/Layout";
import Landing from "../components/Landing/Landing";
import { collectionFetcher } from "../lib/api/CollectionApi";
import { CollectionResult } from "../types/CollectionQuery";
import Error from "./_error";

export async function getServerSideProps() {
  // Fetch all collections
  const collectionResult: CollectionResult = await collectionFetcher({
    perPage: 8,
  });

  return {
    props: {
      collections: collectionResult.collections,
      statusCode: collectionResult.statusCode,
    },
  };
}

const LandingPage: React.FC<any> = (props) => {
  if (props.statusCode) {
    return <Error statusCode={props.statusCode} />;
  }

  return (
    <Layout>
      <Landing collections={props.collections} />
    </Layout>
  );
};

export default LandingPage;

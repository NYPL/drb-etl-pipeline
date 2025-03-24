import React from "react";
import { ApiSearchQuery } from "~/src/types/SearchQuery";
import Link from "~/src/components/Link/Link";

const Author: React.FC<{ author: string }> = ({ author }) => {
  if (!author) return null;
  const query: ApiSearchQuery = {
    query: `author:${author}`,
  };
  return (
    <Link
      to={{
        pathname: "/search",
        query: query,
      }}
    >
      {author}
    </Link>
  );
};

export default Author;

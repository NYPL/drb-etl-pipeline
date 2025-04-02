import React from "react";
import {
  Card,
  CardContent,
  CardHeading,
} from "@nypl/design-system-react-components";
import { Opds2Feed } from "~/src/types/OpdsModel";
import { truncateStringOnWhitespace } from "~/src/util/Util";
import {
  MAX_DESCRIPTION_LENGTH,
  MAX_COLLECTION_TITLE_LENGTH,
  PLACEHOLDER_LINK,
} from "~/src/constants/collection";

export const CollectionCard: React.FC<{ collection: Opds2Feed }> = ({
  collection,
}) => {
  return (
    <Card
      layout="column"
      imageProps={{
        src: PLACEHOLDER_LINK,
        alt: ``,
        aspectRatio: "twoByOne",
      }}
      mainActionLink={collection.links[0].href}
      isBordered
      minHeight="405px"
    >
      <CardHeading
        level="h3"
        size="heading5"
        id="stack1-heading1"
        overline="Collection"
        subtitle={collection.metadata.numberOfItems + " Items"}
      >
        {truncateStringOnWhitespace(
          collection.metadata.title,
          MAX_COLLECTION_TITLE_LENGTH
        )}
      </CardHeading>
      <CardContent>
        {truncateStringOnWhitespace(
          collection.metadata.description,
          MAX_DESCRIPTION_LENGTH
        )}
      </CardContent>
    </Card>
  );
};

export default CollectionCard;

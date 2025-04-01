import React from "react";
import {
  Box,
  SimpleGrid,
  useNYPLBreakpoints,
} from "@nypl/design-system-react-components";
import CollectionCard from "../CollectionCard/CollectionCard";
import { Opds2Feed } from "~/src/types/OpdsModel";
import { MAX_COLLECTION_LIST_LENGTH } from "~/src/constants/collection";

export const CollectionList: React.FC<{ collections: Opds2Feed }> = ({
  collections,
}) => {
  const { isLargerThanMedium, isLargerThanLarge, isLargerThanXLarge } =
    useNYPLBreakpoints();
  let numberOfColumns = 4;
  if (isLargerThanXLarge) {
    numberOfColumns = 4;
  } else if (isLargerThanLarge) {
    numberOfColumns = 3;
  } else if (isLargerThanMedium) {
    numberOfColumns = 2;
  } else {
    numberOfColumns = 1;
  }

  return (
    <Box>
      {collections && collections.groups ? (
        <>
          <SimpleGrid gap="grid.l" columns={numberOfColumns}>
            {collections.groups.map((collection, index) => {
              if (index < MAX_COLLECTION_LIST_LENGTH)
                return (
                  <CollectionCard
                    key={"collection-card-" + index}
                    collection={collection}
                  />
                );
            })}
          </SimpleGrid>
          {/* todo: Add in a future iteration of collections (SFR-1637)
          {collections.groups.length > MAX_COLLECTION_LIST_LENGTH && (
            <Link
              type="forwards"
              href="/collections"
              marginTop="m"
              float="right"
            >
              View All Collections
            </Link>
          )} */}
        </>
      ) : (
        "No collections available"
      )}
    </Box>
  );
};

export default CollectionList;

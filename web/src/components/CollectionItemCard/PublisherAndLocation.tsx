import React from "react";
import { Box } from "@nypl/design-system-react-components";
import CollectionUtils from "~/src/util/CollectionUtils";

const PublisherAndLocation: React.FC<{
  pubPlace: string;
  publisher: string;
}> = ({ pubPlace, publisher }) => {
  const displayLocation = CollectionUtils.getPublisherDisplayLocation(pubPlace);
  const displayName = CollectionUtils.getPublisherDisplayText(publisher);

  return (
    <Box as="p" margin="0">
      {displayLocation && displayName
        ? `Published${displayLocation}${displayName}`
        : "Publisher and Location Unknown"}
    </Box>
  );
};

export default PublisherAndLocation;

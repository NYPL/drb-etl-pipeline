import React from "react";
import { Agent } from "~/src/types/DataModel";
import EditionCardUtils from "~/src/util/EditionCardUtils";

const PublisherAndLocation: React.FC<{
  pubPlace: string;
  publishers: Agent[];
}> = ({ pubPlace, publishers }) => {
  const displayLocation =
    EditionCardUtils.getPublisherDisplayLocation(pubPlace) || "";

  const displayName =
    EditionCardUtils.getPublishersDisplayText(publishers) || "";

  return (
    <>
      {!displayLocation && !displayName
        ? "Publisher and Location Unknown"
        : `Published${displayLocation}${displayName}`}
    </>
  );
};

export default PublisherAndLocation;

import { Box } from "@nypl/design-system-react-components";
import React from "react";
import Link from "~/src/components/Link/Link";
import { Instance } from "~/src/types/DataModel";
import EditionCardUtils from "~/src/util/EditionCardUtils";

const WorldCat: React.FC<{
  instance: Instance;
}> = ({ instance }) => {
  const oclcLink = EditionCardUtils.getOclcLink(instance);
  return (
    <Box>
      {oclcLink ? (
        <Link to={oclcLink}>Find in a library</Link>
      ) : (
        <>Find in Library Unavailable</>
      )}
    </Box>
  );
};

export default WorldCat;

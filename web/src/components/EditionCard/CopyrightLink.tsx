import React from "react";
import { Rights } from "~/src/types/DataModel";
import Link from "~/src/components/Link/Link";

const CopyrightLink: React.FC<{ rights: Rights[] }> = ({ rights }) => {
  return (
    <Link to="/copyright">
      {rights && rights.length > 0
        ? `Copyright: ${rights[0].rightsStatement}`
        : "Copyright: Unknown"}
    </Link>
  );
};

export default CopyrightLink;

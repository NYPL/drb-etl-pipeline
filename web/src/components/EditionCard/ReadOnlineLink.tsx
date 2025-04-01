import { Box } from "@nypl/design-system-react-components";
import React from "react";
import Link from "~/src/components/Link/Link";
import { LOGIN_LINK_BASE } from "~/src/constants/links";
import { ItemLink } from "~/src/types/DataModel";
import { LOGIN_TO_READ_TEST_ID } from "~/src/constants/testIds";

// "Read Online" button should only show up if the link was flagged as "reader" or "embed"
const ReadOnlineLink: React.FC<{
  readOnlineLink: ItemLink;
  isLoggedIn: boolean;
  title: string;
  loginCookie?: any;
}> = ({ readOnlineLink, isLoggedIn, title }) => {
  let linkText = "Read Online";
  let linkUrl: any = {
    pathname: `/read/${readOnlineLink.link_id}`,
  };

  if (
    (readOnlineLink.flags.nypl_login ||
      readOnlineLink.flags.fulfill_limited_access) &&
    !isLoggedIn
  ) {
    linkText = "Log in to read online";
    linkUrl = LOGIN_LINK_BASE + encodeURIComponent(window.location.href);
  }

  return (
    readOnlineLink && (
      <Box data-testid={LOGIN_TO_READ_TEST_ID}>
        <Link
          to={linkUrl}
          linkType="button"
          aria-label={`${title} ${linkText}`}
        >
          {linkText}
        </Link>
      </Box>
    )
  );
};

export default ReadOnlineLink;

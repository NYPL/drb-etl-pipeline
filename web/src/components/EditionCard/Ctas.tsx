import React from "react";
import { useCookies } from "react-cookie";
import { NYPL_SESSION_ID } from "~/src/constants/auth";
import { ApiItem } from "~/src/types/DataModel";
import EditionCardUtils from "~/src/util/EditionCardUtils";
import DownloadLink from "./DownloadLink";
import EddLink from "./EddLink";
import ReadOnlineLink from "./ReadOnlineLink";

const Ctas: React.FC<{
  item: ApiItem | undefined;
  title: string;
}> = ({ item, title }) => {
  // cookies defaults to be undefined if not fonud
  const [cookies] = useCookies([NYPL_SESSION_ID]);
  const loginCookie = cookies[NYPL_SESSION_ID];
  const isLoggedIn = !!loginCookie;

  const readOnlineLink = EditionCardUtils.getReadOnlineLink(item);
  const downloadLink = EditionCardUtils.selectDownloadLink(item);

  if (readOnlineLink || downloadLink) {
    return (
      <>
        {readOnlineLink && (
          <ReadOnlineLink
            readOnlineLink={readOnlineLink}
            isLoggedIn={isLoggedIn}
            title={title}
          />
        )}
        {downloadLink && (
          <DownloadLink
            downloadLink={downloadLink}
            title={title}
            isLoggedIn={isLoggedIn}
            loginCookie={loginCookie}
          />
        )}
      </>
    );
  }

  const eddLink =
    item && item.links ? item.links.find((link) => link.flags.edd) : undefined;

  // Offer EDD if available
  if (eddLink !== undefined) {
    return <EddLink eddLink={eddLink} isLoggedIn={isLoggedIn} title={title} />;
  }

  return <>Not yet available</>;
};

export default Ctas;

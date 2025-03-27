import React, { useState } from "react";
import { formatUrl } from "~/src/util/Util";
import Loading from "../Loading/Loading";

const IFrameReader: React.FC<{ url: string }> = (props) => {
  const url = props.url;
  const [loading, setLoading] = useState(true);
  return (
    <>
      {loading && <Loading />}
      {url && (
        <iframe
          className="iframe-reader"
          onLoad={() => setLoading(false)}
          allowFullScreen
          src={`${formatUrl(url)}`}
          title="Ebook Frame"
        />
      )}
    </>
  );
};

export default IFrameReader;

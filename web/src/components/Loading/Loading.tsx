import React from "react";

import BookSvg from "../Svgs/BookSvg";
const Loading: React.FC = () => (
  <div
    aria-label="loading"
    className="loading"
    role="alert"
    aria-live="assertive"
  >
    <div className="loading-place">
      <div className="loading-front">
        <BookSvg fill="#0071ce" />
      </div>

      <div className="curtain">
        <div className="loading-back">
          <BookSvg />
        </div>
      </div>
    </div>
  </div>
);

export default Loading;

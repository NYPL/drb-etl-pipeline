import React from "react";

const TotalWorks: React.FC<{ totalWorks: number }> = ({ totalWorks }) => {
  return (
    <div>{totalWorks && <span>Total number of works: {totalWorks}</span>}</div>
  );
};

export default TotalWorks;

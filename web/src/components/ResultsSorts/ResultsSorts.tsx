import React from "react";
import { Fieldset, Select } from "@nypl/design-system-react-components";
import { numbersPerPage } from "~/src/constants/sorts";
import { deepEqual } from "~/src/util/Util";
import { Sort } from "~/src/types/DataModel";

const ResultsSorts: React.FC<{
  perPage: number;
  sort: Sort;
  sortMap: { [key: string]: Sort };
  isModal?: boolean;
  onChangePerPage: (e) => void;
  onChangeSort: (e) => void;
}> = ({ perPage, sort, sortMap, isModal, onChangePerPage, onChangeSort }) => {
  return (
    <Fieldset
      id="sort-fieldset"
      display="flex"
      alignItems="center"
      flexDir={{ base: "column", md: "row" }}
      gap="s"
    >
      <Select
        id={isModal ? "items-per-page-modal" : "items-per-page"}
        name="itemsPerPageSelect"
        isRequired={false}
        labelText="Items Per Page"
        labelPosition="inline"
        value={perPage.toString()}
        onChange={(e) => onChangePerPage(e)}
        width="100%"
      >
        {numbersPerPage.map((pageNum: string) => {
          return <option key={`per-page-${pageNum}`}>{pageNum}</option>;
        })}
      </Select>
      <Select
        id={isModal ? "sort-by-modal" : "sort-by"}
        name="sortBySelect"
        isRequired={false}
        labelText="Sort By"
        labelPosition="inline"
        value={Object.keys(sortMap).find((key) =>
          deepEqual(sortMap[key], sort)
        )}
        onChange={(e) => onChangeSort(e)}
        width="100%"
      >
        {Object.keys(sortMap).map((sortOption: string) => {
          return (
            <option key={`sort-option-${sortOption}`}>{sortOption}</option>
          );
        })}
      </Select>
    </Fieldset>
  );
};

export default ResultsSorts;

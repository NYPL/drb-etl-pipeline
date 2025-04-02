import { Checkbox, CheckboxGroup } from "@nypl/design-system-react-components";
import React from "react";
import { Filter } from "~/src/types/SearchQuery";
import { FormatTypes } from "~/src/constants/labels";

// A Checkbox List of formats
const FilterBookFormat: React.FC<{
  selectedFormats: Filter[];
  isModal?: boolean;
  onFormatChange: (e, format: string) => void;
}> = (props) => {
  const { selectedFormats, isModal, onFormatChange } = props;

  const isSelected = (formats: Filter[], format: string) => {
    const selected = formats.find((selectedFormat) => {
      return selectedFormat.value === format;
    });
    return !!selected;
  };

  const toggleSelected = (e, format) => {
    onFormatChange(e, format);
  };

  return (
    <CheckboxGroup
      labelText="Format"
      id={isModal ? "format-checkbox-group-modal" : "format-checkbox-group"}
      name="Format Checkbox Group"
    >
      {FormatTypes.map((formatType: any) => (
        <Checkbox
          key={"checkbox-" + formatType.label}
          labelText={formatType.label}
          onChange={(e) => toggleSelected(e, formatType.value)}
          isChecked={isSelected(selectedFormats, formatType.value)}
          id={
            isModal
              ? formatType.label + "-modal-checkbox"
              : formatType.label + "-checkbox"
          }
        />
      ))}
    </CheckboxGroup>
  );
};

export default FilterBookFormat;

import { FacetItem } from "~/src/types/DataModel";
import {
  Accordion,
  Checkbox,
  CheckboxGroup,
} from "@nypl/design-system-react-components";
import React from "react";
import { Filter } from "~/src/types/SearchQuery";

// An Accordion of languages

function areEqual(
  prevProps: {
    languages: FacetItem[];
    showCount: boolean;
    selectedLanguages: Filter[];
    onLanguageChange: any;
  },
  nextProps: {
    languages: FacetItem[];
    showCount: boolean;
    selectedLanguages: Filter[];
    onLanguageChange: any;
  }
) {
  return (
    prevProps.languages === nextProps.languages &&
    prevProps.selectedLanguages.length === nextProps.selectedLanguages.length
  );
}

const LanguageAccordion: React.FC<{
  languages: FacetItem[];
  showCount: boolean;
  selectedLanguages: Filter[];
  isModal?: boolean;
  onLanguageChange: (e, language: string) => void;
}> = (props) => {
  const { languages, showCount, selectedLanguages, isModal, onLanguageChange } =
    props;

  const selectedLanguageFilter = (language: string) => {
    return selectedLanguages.find((langFilter) => {
      return langFilter.value === language;
    });
  };

  const toggleSelected = (
    e: React.ChangeEvent<HTMLInputElement>,
    language: string
  ) => {
    onLanguageChange(e, language);
  };

  return (
    <Accordion
      accordionData={[
        {
          label: "Filter Languages",
          panel: (
            <CheckboxGroup
              labelText="List of Languages"
              layout="column"
              name="languages-list"
              showRequiredLabel={false}
              showLabel={false}
              id={
                isModal
                  ? "languages-checkbox-group-modal"
                  : "languages-checkbox-group"
              }
            >
              {languages.map((language) => {
                return (
                  <Checkbox
                    key={`check-${language.value}`}
                    name="Languages"
                    labelText={`${language.value} ${
                      showCount ? "(" + language.count + ")" : ""
                    }`}
                    isChecked={!!selectedLanguageFilter(language.value)}
                    onChange={(e) => toggleSelected(e, language.value)}
                    id={
                      isModal
                        ? language.value + "-modal-checkbox"
                        : language.value + "-checkbox"
                    }
                  />
                );
              })}
            </CheckboxGroup>
          ),
        },
      ]}
      bg="ui.white"
      isDefaultOpen={true}
    />
  );
};

export default React.memo(LanguageAccordion, areEqual);

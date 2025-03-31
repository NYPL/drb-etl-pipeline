import React from "react";
import {
  Box,
  Heading,
  Hero,
  TemplateAppContainer,
  useNYPLBreakpoints,
} from "@nypl/design-system-react-components";
import SearchForm from "~/src/components/SearchForm/SearchForm";
import CollectionList from "../CollectionList/CollectionList";
import { Opds2Feed } from "~/src/types/OpdsModel";
import DrbHero from "../DrbHero/DrbHero";
import DrbBreakout from "../DrbBreakout/DrbBreakout";
import Link from "../Link/Link";

const LandingPage: React.FC<{ collections?: Opds2Feed }> = ({
  collections,
}) => {
  const subHeader = (
    <Box
      sx={{
        a: {
          color: "ui.link.primary",
          display: "inline",
        },
      }}
    >
      <span>
        Find millions of digital books for research from multiple sources
        world-wide--all free to read, download, and keep. No library card
        required. This is an early beta test, so we want your feedback!{" "}
        <Link to="/about">Read more about the project</Link>.
      </span>
      <Box marginTop="s">
        <SearchForm />
      </Box>
    </Box>
  );

  const {
    isLargerThanMedium,
    isLargerThanMobile,
    isLargerThanLarge,
    isLargerThanXLarge,
  } = useNYPLBreakpoints();

  let backgroundImageSrc =
    "https://drb-files-qa.s3.amazonaws.com/hero/heroDesktop2x.jpg";
  if (isLargerThanXLarge) {
    backgroundImageSrc =
      "https://drb-files-qa.s3.amazonaws.com/hero/heroDesktop2x.jpg";
  } else if (isLargerThanLarge) {
    backgroundImageSrc =
      "https://drb-files-qa.s3.amazonaws.com/hero/heroDesktop.jpg";
  } else if (isLargerThanMedium) {
    backgroundImageSrc =
      "https://drb-files-qa.s3.amazonaws.com/hero/heroTabletLarge.jpg";
  } else if (isLargerThanMobile) {
    backgroundImageSrc =
      "https://drb-files-qa.s3.amazonaws.com/hero/heroTabletSmall.jpg";
  } else {
    backgroundImageSrc =
      "https://drb-files-qa.s3.amazonaws.com/hero/heroMobile.jpg";
  }

  const breakoutElement = (
    <DrbBreakout>
      <DrbHero />
      <Hero
        backgroundColor="ui.gray.light-cool"
        backgroundImageSrc={backgroundImageSrc}
        foregroundColor="ui.black"
        heroType="primary"
        heading={
          <Heading
            level="h1"
            size="heading2"
            id="primary-hero"
            color="ui.black"
          >
            Search the World&apos;s Research Collections
          </Heading>
        }
        subHeaderText={subHeader}
      />
    </DrbBreakout>
  );

  const contentPrimaryElement = (
    <Box marginLeft="l" marginRight="l">
      <Heading level="h2">Recently Added Collections</Heading>
      <CollectionList collections={collections} />
    </Box>
  );
  return (
    <TemplateAppContainer
      breakout={breakoutElement}
      contentPrimary={contentPrimaryElement}
    />
  );
};

export default LandingPage;

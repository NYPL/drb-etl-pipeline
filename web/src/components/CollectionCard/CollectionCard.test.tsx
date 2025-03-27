import React from "react";
import CollectionCard from "./CollectionCard";
import { screen } from "@testing-library/react";
import { collectionData } from "~/src/__tests__/fixtures/CollectionFixture";
import { render } from "~/src/__tests__/testUtils/render";

describe("Collection list", () => {
  beforeEach(() => {
    render(<CollectionCard collection={collectionData.collections} />);
  });
  test("shows Title as heading", () => {
    expect(
      screen.getByRole("heading", {
        name: "Baseball: A Collection by Mike Benowitz",
      })
    ).toBeInTheDocument();
  });
  test("shows Description", () => {
    expect(
      screen.getByText("A history of the sport of baseball")
    ).toBeInTheDocument();
  });
  test("Shows cover", () => {
    expect(screen.getByAltText("").closest("img").src).toEqual(
      "https://drb-files-qa.s3.amazonaws.com/misc/collectionPlaceholder.jpg"
    );
  });
  test("Shows number of items", () => {
    expect(screen.getByText("3 Items")).toBeInTheDocument();
  });
});

import React from "react";
import CollectionList from "./CollectionList";
import { screen } from "@testing-library/react";
import { oneCollectionListData } from "~/src/__tests__/fixtures/CollectionFixture";
import { render } from "~/src/__tests__/testUtils/render";

// describe("Collection list", () => {
//   beforeEach(() => {
//     render(<CollectionList collections={collectionListData} />);
//   });
// todo: Add in a future iteration of collections (SFR-1637)
// test("shows View All Collections link", () => {
//   expect(
//     screen.getByRole("link", { name: "View All Collections" })
//   ).toBeInTheDocument();
// });
// });

describe("Collection list with one item", () => {
  beforeEach(() => {
    render(<CollectionList collections={oneCollectionListData} />);
  });
  test("does not show View All Collections link", () => {
    expect(
      screen.queryByRole("link", { name: "View All Collections" })
    ).not.toBeInTheDocument();
  });
});

describe("Collection list with no data", () => {
  beforeEach(() => {
    render(<CollectionList collections={null} />);
  });
  test("shows No collections available", () => {
    expect(screen.getByText("No collections available")).toBeInTheDocument();
  });
});

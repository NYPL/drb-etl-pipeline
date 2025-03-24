import { screen } from "@testing-library/react";
import React from "react";
import { render } from "~/src/__tests__/testUtils/render";
import Loading from "./Loading";

describe("Loading page", () => {
  beforeEach(() => {
    render(<Loading />);
  });

  it("should have an 'alert' element", () => {
    expect(screen.getByRole("alert", { name: "loading" })).toBeInTheDocument();
  });
});

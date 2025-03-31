import React from "react";
import { render } from "~/src/__tests__/testUtils/render";
import AboutPage from "./About";

it("renders about unchanged", async () => {
  const tree = render(<AboutPage />);
  expect(tree.container.firstChild).toMatchSnapshot();
});

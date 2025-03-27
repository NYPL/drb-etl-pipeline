import React from "react";
import { render } from "~/src/__tests__/testUtils/render";
import { screen } from "@testing-library/react";
import Copyright from "./Copyright";

it("renders Copyright page unchanged", async () => {
  const tree = render(<Copyright />);
  expect(tree.container.firstChild).toMatchSnapshot();
});

describe("Copyright Page", () => {
  beforeEach(() => {
    render(<Copyright />);
  });

  it("renders the Copyright Explanations heading", () => {
    expect(
      screen.getByRole("heading", { name: "Copyright Explanations" })
    ).toBeInTheDocument();
  });

  it("renders the Public Domain headings", () => {
    expect(
      screen.getByRole("heading", { name: "Public Domain" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Public Domain (US Only)" })
    ).toBeInTheDocument();
  });

  it("renders the Creative Commons section", () => {
    expect(
      screen.getByRole("heading", { name: "Creative Commons Licenses" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Creative Commons licenses" })
    ).toHaveAttribute("href", "https://creativecommons.org/");

    expect(
      screen.getByRole("link", { name: "Attribution 3.0 Unported (CC BY 3.0)" })
    ).toHaveAttribute("href", "https://creativecommons.org/licenses/by/3.0/");
  });

  it("renders the CC0 section", () => {
    expect(
      screen.getByRole("heading", { name: "CC0 Public Domain Dedication" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
      })
    ).toHaveAttribute(
      "href",
      "https://creativecommons.org/publicdomain/zero/1.0/"
    );
  });

  it("renders the GNU section", () => {
    expect(
      screen.getByRole("heading", { name: "GNU General Public License" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "GNU General Public License",
      })
    ).toHaveAttribute("href", "http://www.gnu.org/licenses/gpl.html");
  });

  it("renders the In Copyright heading", () => {
    expect(
      screen.getByRole("heading", { name: "In Copyright" })
    ).toBeInTheDocument();
  });
});

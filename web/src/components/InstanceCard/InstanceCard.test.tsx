import React from "react";
import { InstanceCard } from "./InstanceCard";
import { screen } from "@testing-library/react";
import { Instance, WorkEdition } from "~/src/types/DataModel";
import { PLACEHOLDER_COVER_LINK } from "~/src/constants/editioncard";
import {
  fullEdition,
  upEdition,
} from "~/src/__tests__/fixtures/EditionCardFixture";
import { NYPL_SESSION_ID } from "~/src/constants/auth";
import {
  fullInstance,
  eddInstance,
  upInstance,
} from "~/src/__tests__/fixtures/InstanceCardFixture";
import { Cookies, CookiesProvider } from "react-cookie";
import { render } from "~/src/__tests__/testUtils/render";

describe("Instance Card with Valid Data", () => {
  beforeEach(() => {
    render(<InstanceCard edition={fullEdition} instance={fullInstance} />);
  });
  test("Shows year as header", () => {
    expect(screen.getByRole("heading", { name: "1990" })).toBeInTheDocument();
  });
  test("Shows full publisher", () => {
    expect(
      screen.getByText("Published in Paris by publisher_1")
    ).toBeInTheDocument();
  });
  test("Shows link to worldcat", () => {
    expect(screen.getByText("Find in a library").closest("a").href).toContain(
      "www.worldcat.org"
    );
  });
  test("Shows cover", () => {
    expect(screen.getByAltText("").closest("img").src).toEqual(
      "https://test-cover/"
    );
  });
  test("shows license", () => {
    expect(
      screen.getByText("Copyright: test rights statement").closest("a").href
    ).toContain("/copyright");
  });
});

describe("Instance Card with Minmal Data", () => {
  const emptyEdition: WorkEdition = {
    edition_id: 1189584,
  };
  const emptyInstance: Instance = {
    instance_id: 12345,
  };
  beforeEach(() => {
    render(<InstanceCard edition={emptyEdition} instance={emptyInstance} />);
  });
  test("Shows year as header", () => {
    expect(
      screen.getByRole("heading", { name: "Edition Year Unknown" })
    ).toBeInTheDocument();
  });
  test("Shows placeholder publisher", () => {
    expect(
      screen.getByText("Publisher and Location Unknown")
    ).toBeInTheDocument();
  });
  test("Shows Placeholder worldcat text", () => {
    expect(screen.getByText("Find in Library Unavailable")).toBeInTheDocument();
  });
  test("Shows cover", () => {
    expect(screen.getByAltText("").closest("img").src).toEqual(
      PLACEHOLDER_COVER_LINK
    );
  });
  test("shows license", () => {
    expect(screen.getByText("Copyright: Unknown").closest("a").href).toContain(
      "/copyright"
    );
  });
});

describe("Instance with EDD", () => {
  test("Shows Download and Read Online button when edition has both EDD and readable links", () => {
    render(
      <InstanceCard
        edition={fullEdition}
        instance={fullInstance}
      ></InstanceCard>
    );

    expect(screen.getByText("Download PDF")).toBeInTheDocument();
    expect(screen.getByText("Read Online")).toBeInTheDocument();
    expect(screen.queryByText("Log in for options")).not.toBeInTheDocument();
    expect(screen.queryByText("Request Scan")).not.toBeInTheDocument();
  });

  test("Shows Login button when EDD is available but user is not logged in", () => {
    render(
      <InstanceCard edition={fullEdition} instance={eddInstance}></InstanceCard>
    );
    expect(
      screen.getByRole("link", { name: "Log in to request scan for title" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Log in to request scan for title" })
    ).toHaveAttribute(
      "href",
      expect.stringContaining("https://login.nypl.org/auth/login")
    );
    expect(screen.queryByText("Download PDF")).not.toBeInTheDocument();
    expect(screen.queryByText("Read Online")).not.toBeInTheDocument();
  });

  test("Shows EDD Request button when user is logged in", () => {
    // Set cookie before rendering the component
    const cookies = new Cookies();
    cookies.set(NYPL_SESSION_ID, "randomvalue");
    render(
      <CookiesProvider cookies={cookies}>
        <InstanceCard
          edition={fullEdition}
          instance={eddInstance}
        ></InstanceCard>
      </CookiesProvider>
    );

    expect(
      screen.getByRole("link", { name: "Request scan for title" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Request scan for title" })
    ).toHaveAttribute("href", expect.stringContaining("test-link-url"));
    expect(screen.queryByText("Download PDF")).not.toBeInTheDocument();
    expect(screen.queryByText("Read Online")).not.toBeInTheDocument();
  });

  test("Shows 'Physical Edition' badge and 'Scan and Deliver' link", () => {
    render(<InstanceCard edition={fullEdition} instance={eddInstance} />);
    expect(screen.getByText("Physical Edition")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Scan and Deliver" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Scan and Deliver" })
    ).toHaveAttribute("href", "https://www.nypl.org/research/scan-and-deliver");
  });
});

describe("Instance with UP", () => {
  test("Shows Login button when user is not logged in", () => {
    render(<InstanceCard edition={upEdition} instance={upInstance} />);
    expect(
      screen.getByRole("link", { name: "title Log in to read online" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "title Log in to read online" })
    ).toHaveAttribute(
      "href",
      expect.stringContaining("https://login.nypl.org/auth/login")
    );
    expect(screen.queryByText("Download PDF")).not.toBeInTheDocument();
    expect(screen.queryByText("Read Online")).not.toBeInTheDocument();
  });
  test("Shows 'Library Card Required' badge", () => {
    render(<InstanceCard edition={upEdition} instance={upInstance} />);
    expect(screen.getByText("LIBRARY CARD REQUIRED")).toBeInTheDocument();
  });
  test("Shows Read Online and Download buttons when user is logged in", () => {
    // Set cookie before rendering the component
    const cookies = new Cookies();
    cookies.set(NYPL_SESSION_ID, "randomvalue");
    render(
      <CookiesProvider cookies={cookies}>
        <InstanceCard edition={upEdition} instance={upInstance} />
      </CookiesProvider>
    );

    expect(
      screen.getByRole("link", { name: "title Read Online" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "title Read Online" })
    ).toHaveAttribute("href", expect.stringContaining("/read/12"));
    expect(
      screen.getByRole("link", { name: "title Download PDF" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "title Download PDF" })
    ).toHaveAttribute("href", expect.stringContaining("test-link-url"));
  });
  test("Shows blurb with publisher", () => {
    render(<InstanceCard edition={upEdition} instance={upInstance} />);
    expect(
      screen.getByText("Digitalized by NYPL with permission of publisher_1")
    ).toBeInTheDocument();
  });
});

import React from "react";
import WorkDetailDefinitionList from "./WorkDetailDefinitionList";
import { screen } from "@testing-library/react";
import { ApiWork } from "~/src/types/WorkQuery";
import { workDetail as apiWork } from "../../__tests__/fixtures/WorkDetailFixture";
import { render } from "~/src/__tests__/testUtils/render";

describe("Work Detail table with all information", () => {
  beforeEach(() => {
    render(
      <WorkDetailDefinitionList work={apiWork.data}></WorkDetailDefinitionList>
    );
  });
  test("shows heading", () => {
    expect(
      screen.getByRole("heading", { name: "Details" })
    ).toBeInTheDocument();
  });
  test("Alt titles link to title search", () => {
    expect(screen.getByText("Alternative Titles")).toBeInTheDocument();
    expect(screen.getByText("Alt title 1").closest("a").href).toContain(
      `/search?query=title%3AAlt+title+1`
    );
    expect(screen.getByText("Alt title 2").closest("a").href).toContain(
      `/search?query=title%3AAlt+title+2`
    );
  });
  test("shows series and position", () => {
    expect(screen.getByText("Series")).toBeInTheDocument();
    expect(
      screen.getByText("The modern library classics vol. VIII")
    ).toBeInTheDocument();
  });
  test("Authors link to author search", () => {
    expect(screen.getByText("Authors")).toBeInTheDocument();
    expect(
      screen.getByText("McClure, H. David. ()").closest("a").href
    ).toContain(`/search?query=author%3AMcClure%2C+H.+David.+%28%29`);
  });
  test("Shows subjects as links to search", () => {
    expect(
      screen.getByText("Readers (Publications)").closest("a").href
    ).toContain("/search?query=subject%3AReaders+%28Publications%29");
    expect(screen.getByText("Joruba (taal)").closest("a").href).toContain(
      "/search?query=subject%3AJoruba+%28taal%29"
    );
    expect(screen.getByText("Yoruba (langue)").closest("a").href).toContain(
      "/search?query=subject%3AYoruba+%28langue%29"
    );
    expect(screen.getByText("Yoruba language").closest("a").href).toContain(
      "/search?query=subject%3AYoruba+language"
    );
    expect(screen.getByText("more subjects").closest("a").href).toContain(
      "/search?query=subject%3Amore+subjects"
    );
    expect(screen.getByText("Textbooks").closest("a").href).toContain(
      "/search?query=subject%3ATextbooks"
    );
    expect(screen.getByText("Texts (form)").closest("a").href).toContain(
      "/search?query=subject%3ATexts+%28form%29"
    );
    expect(screen.getByText("Readers").closest("a").href).toContain(
      "/search?query=subject%3AReaders"
    );
  });
  test("shows languages", () => {
    expect(screen.getByText("Languages")).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("listitem")
        .find((listitem) => listitem.textContent === "English")
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByRole("listitem")
        .find((listitem) => listitem.textContent === "German")
    ).toBeInTheDocument();
  });
});

describe("Work Detail table with minimal information", () => {
  const emptyApiWork: ApiWork = {};
  beforeEach(() => {
    render(
      <WorkDetailDefinitionList work={emptyApiWork}></WorkDetailDefinitionList>
    );
  });
  test("shows heading", () => {
    expect(
      screen.getByRole("heading", { name: "Details" })
    ).toBeInTheDocument();
  });
  test("Alt titles does not show up", () => {
    expect(screen.queryByText("Alternative Titles")).not.toBeInTheDocument();
  });
  test("Does not show series", () => {
    expect(screen.queryByText("Series")).not.toBeInTheDocument();
  });
  test("Shows Unknown authors", () => {
    expect(screen.getByText("Authors")).toBeInTheDocument();
  });
  test("Does not show subjects", () => {
    expect(screen.queryByText("Subjects")).not.toBeInTheDocument();
  });
  test("Does not show languages", () => {
    expect(screen.queryByText("Languages")).not.toBeInTheDocument();
  });
});

describe("Work detail edge cases", () => {
  test("Eliminates duplicated subjects", () => {
    const duplicateSubjectWork: ApiWork = {
      subjects: [
        {
          heading: "United States",
          authority: "fast",
          controlNo: "1204155",
        },
        {
          heading: "United States",
          authority: "fast",
          controlNo: "1204155",
        },
      ],
    };
    render(
      <WorkDetailDefinitionList
        work={duplicateSubjectWork}
      ></WorkDetailDefinitionList>
    );

    expect(screen.getByText("Subjects")).toBeInTheDocument();
    expect(screen.getAllByText("United States").length).toEqual(1);
  });

  test("Shows series without position", () => {
    const workWithSeries: ApiWork = {
      series: "Animal Crossing",
    };
    render(
      <WorkDetailDefinitionList
        work={workWithSeries}
      ></WorkDetailDefinitionList>
    );

    expect(screen.getByText("Series")).toBeInTheDocument();
    expect(screen.getByText("Animal Crossing")).toBeInTheDocument();
  });
});

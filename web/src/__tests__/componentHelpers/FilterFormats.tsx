import { screen, within } from "@testing-library/react";

export const FilterFormatTests = () => {
  const formats = screen.getByRole("group", { name: "Format" });
  expect(formats).toBeInTheDocument();
  expect(
    within(formats).getByRole("checkbox", { name: "Readable" })
  ).not.toBeChecked();
  expect(
    within(formats).getByRole("checkbox", { name: "Downloadable" })
  ).not.toBeChecked();
  expect(
    within(formats).getByRole("checkbox", { name: "Requestable" })
  ).not.toBeChecked();
};

import { test, expect } from "../support/test-utils";
import { INVALID_COLLECTION_PATH, HOME_PATH } from "~/mocks/mockEnv";
import { server } from "~/mocks/server";
import {
  SEARCH_BAR_TEST_ID,
  ERROR_LAYOUT_TEST_ID,
} from "~/src/constants/testIds";

test.afterEach(() => server.resetHandlers());
test.afterAll(() => server.close());

test("View landing page with search", async ({ page }) => {
  await page.goto(`${HOME_PATH}`);

  const searchBar = page.getByTestId(SEARCH_BAR_TEST_ID);
  await expect(searchBar).toBeVisible();
});

test("Shows error page for invalid collection", async ({ page }) => {
  await page.goto(`${INVALID_COLLECTION_PATH}`);

  const errorLayout = page.getByTestId(ERROR_LAYOUT_TEST_ID);
  await expect(errorLayout).toBeVisible();
});

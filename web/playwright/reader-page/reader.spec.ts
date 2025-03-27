import { test } from "@playwright/test";
import { ReaderPage } from "./reader-page";

test.describe("e-Reader validation", () => {
  test("Validate all the features of e-Reader is displayed", async ({
    page,
  }) => {
    const readerPage = new ReaderPage(page);
    await readerPage.navigateToHome();
    await readerPage.fillSearchBox("Robot Soccer");
    await readerPage.clickSearchButton();
    await readerPage.verifyRobotSoccerTitleVisible();
    await readerPage.verifyFirstReadOnlineButtonVisible();
  });
});

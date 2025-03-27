import { test } from "@playwright/test";
import { CopyrightPage } from "./copyright-page";

test.describe("License Page", () => {
  test("Verify the headers and subheaders of DRB Copyright Page", async ({
    page,
  }) => {
    const copyrightPage = new CopyrightPage(page);
    await copyrightPage.navigateToCopyrightPage();
    await copyrightPage.verifyHeaderVisible(
      copyrightPage.copyrightExplanationsHeader
    );
    await copyrightPage.verifyHeaderVisible(copyrightPage.publicDomainHeader);
    await copyrightPage.verifyHeaderVisible(
      copyrightPage.publicDomainUsOnlyHeader
    );
    await copyrightPage.verifyHeaderVisible(
      copyrightPage.creativeCommonsLicensesHeader
    );
  });

  test("Verify the subheaders of DRB Copyright Page are displayed correctly", async ({
    page,
  }) => {
    const copyrightPage = new CopyrightPage(page);
    await copyrightPage.navigateToCopyrightPage();
    await copyrightPage.verifySubheaderVisible(
      copyrightPage.publicDomainSubheader
    );
    await copyrightPage.verifySubheaderVisible(
      copyrightPage.publicDomainUsOnlySubheader
    );
  });
});

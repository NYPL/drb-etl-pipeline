import { expect, Locator, Page } from "@playwright/test";

class CopyrightPage {
  readonly page: Page;
  readonly copyrightExplanationsHeader: Locator;
  readonly publicDomainHeader: Locator;
  readonly publicDomainUsOnlyHeader: Locator;
  readonly creativeCommonsLicensesHeader: Locator;
  readonly publicDomainSubheader: Locator;
  readonly publicDomainUsOnlySubheader: Locator;

  constructor(page: Page) {
    this.page = page;
    this.copyrightExplanationsHeader = page.locator(
      "//h1[text()='Copyright Explanations']"
    );
    this.publicDomainHeader = page.locator("//h2[text()='Public Domain']");
    this.publicDomainUsOnlyHeader = page.locator(
      "//h2[text()='Public Domain (US Only)']"
    );
    this.creativeCommonsLicensesHeader = page.locator(
      "//h2[text()='Creative Commons Licenses']"
    );
    this.publicDomainSubheader = page.locator(
      "//p[contains(text(),'Works may be in the public domain in the Unites St')]"
    );
    this.publicDomainUsOnlySubheader = page.locator(
      "//p[contains(text(),'Works may be in the public domain in the Unites States')]"
    );
  }

  async navigateToCopyrightPage() {
    await this.page.goto("/copyright");
  }

  async verifyHeaderVisible(header: Locator) {
    await expect(header).toBeVisible();
  }

  async verifySubheaderVisible(subheader: Locator) {
    await expect(subheader).toBeVisible();
  }
}

export { CopyrightPage };

import { SITE_SECTION } from "../../constants/analytics";
import { documentTitles } from "../../constants/labels";
import { trackCtaClick, trackPageview } from "./Analytics";

describe("Adobe Analytics", () => {
  beforeEach(() => {
    window.adobeDataLayer = [];
  });

  describe("trackPageview", () => {
    test("it should update window.adobeDataLayer with the approriate values", () => {
      const adobeDataLayer = window.adobeDataLayer;

      trackPageview(documentTitles.workItem);

      const eventData = adobeDataLayer[2];
      const eventValue = eventData.event;
      const pageValue = eventData.page_name;
      const sectionValue = eventData.site_section;

      expect(adobeDataLayer).toHaveLength(3);
      expect(eventValue).toEqual("virtual_page_view");
      expect(pageValue).toEqual(documentTitles.workItem);
      expect(sectionValue).toEqual(SITE_SECTION);
    });
  });

  describe("trackCtaClick", () => {
    test("it should update window.adobeDataLayer with the approriate values", () => {
      const adobeDataLayer = window.adobeDataLayer;

      trackCtaClick({
        cta_section: "Item Title",
        cta_text: "Read Online",
        destination_url: "https://test-destination/",
      });

      const eventData = adobeDataLayer[1];
      const eventValue = eventData.event;
      const eventName = eventData.event_data.name;
      const sectionValue = eventData.event_data.cta_section;
      const textValue = eventData.event_data.cta_text;
      const destinationValue = eventData.event_data.destination_url;

      expect(adobeDataLayer).toHaveLength(2);
      expect(eventValue).toEqual("send_event");
      expect(eventName).toEqual("cta_click");
      expect(sectionValue).toEqual("Item Title");
      expect(textValue).toEqual("Read Online");
      expect(destinationValue).toEqual("https://test-destination/");
    });
  });
});

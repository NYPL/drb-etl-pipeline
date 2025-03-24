import { SITE_SECTION } from "../../constants/analytics";

type EventData = CtaData & {
  name: string;
};

type CtaData = {
  cta_section: string;
  cta_subsection?: string;
  cta_text: string;
  destination_url: string;
};

let hasInitialPageViewFired = false;
/**
 * trackPageview
 * Track an AA pageview.
 * https://blastwiki.atlassian.net/wiki/spaces/NYPL/pages/7898713056053494306/Virtual+Page+View+NYPL
 */
export const trackPageview = (pageName: string) => {
  // First define the global variable for the entire data layer array
  const adobeDataLayer = window.adobeDataLayer || [];
  if (!hasInitialPageViewFired) {
    // push in the variables required in the Initial Data Layer Definition
    adobeDataLayer.push({
      disable_page_view: true,
    });
    hasInitialPageViewFired = true;
  }
  // first clear the data layer of previous values
  adobeDataLayer.push({
    page_name: null,
    site_section: null,
  });
  // then push the new values
  adobeDataLayer.push({
    event: "virtual_page_view",
    page_name: pageName,
    site_section: SITE_SECTION,
  });
};

/**
 * trackEvent
 * Track an AA event.
 * https://blastwiki.atlassian.net/wiki/spaces/NYPL/pages/7898713056053494689/Standard+Events+NYPL
 */
const trackEvent = (eventData: EventData) => {
  // First define the global variable for the entire data layer array
  const adobeDataLayer = window.adobeDataLayer || [];
  //first clear the data layer of previous values
  adobeDataLayer.push({
    event_data: null,
  });
  //then push the new values
  adobeDataLayer.push({
    event: "send_event",
    event_data: eventData,
  });
};

/**
 * trackCtaClick
 * Track an AA CTA Click event.
 * https://blastwiki.atlassian.net/wiki/spaces/NYPL/pages/7898713056053494740/CTA+Click+NYPL
 */
export const trackCtaClick = (ctaData: CtaData) => {
  trackEvent({
    name: "cta_click",
    cta_section: ctaData.cta_section,
    cta_subsection: ctaData.cta_subsection ?? "",
    cta_text: ctaData.cta_text,
    destination_url: ctaData.destination_url,
  });
};

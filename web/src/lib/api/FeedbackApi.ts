import appConfig from "~/config/appConfig";
import { Feedback } from "~/src/types/Feedback";
import { log } from "../newrelic/NewRelic";

// TODO: disable feedback in development

export const submitFeedback = async (feedback: Feedback) => {
  try {
    return await fetch(appConfig.feedback.formURL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.NEXT_PUBLIC_AIRTABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fields: {
          Feedback: feedback.feedback,
          Category: feedback.category,
          Date: new Date().toLocaleDateString("en-US"),
          Environment: process.env.APP_ENV,
          URL: feedback.url,
        },
      }),
    });
  } catch (error) {
    log(error, "Failed to submit feedback");
    throw new Error(`Failed to submit feedback: ${error.message}`);
  }
};

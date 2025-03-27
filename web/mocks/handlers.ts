import { http, HttpResponse, passthrough } from "msw";
import { oneCollectionListData } from "~/src/__tests__/fixtures/CollectionFixture";
import { workDetailWithUp } from "~/src/__tests__/fixtures/WorkDetailFixture";
import {
  API_URL,
  COLLECTION_LIST_PATH,
  INVALID_COLLECTION_PATH,
  DOWNLOAD_PATH,
  FULFILL_PATH,
  WORK_PATH,
} from "./mockEnv";

const isAuthenticated = (request) => {
  const auth = request.headers.get("authorization");
  return auth === "Bearer access-token";
};

const workUrl = new URL(WORK_PATH, API_URL).toString();
const fulfillUrl = new URL(FULFILL_PATH, API_URL).toString();
const downloadUrl = new URL(DOWNLOAD_PATH, API_URL).toString();
const collectionListUrl = new URL(COLLECTION_LIST_PATH, API_URL).toString();
const invalidCollectionUrl = new URL(
  INVALID_COLLECTION_PATH,
  API_URL
).toString();

/** A collection of handlers to be used by default for all tests. */
const handlers = [
  /**
   * Allow normal requests to pass through
   */
  http.all("/_next/*", passthrough),
  http.all("/img/*", passthrough),
  http.all("/__nextjs_original-stack-frame", passthrough),
  http.all("/fonts/*", passthrough),
  http.all("/css/*", passthrough),
  http.get("/js/*", passthrough),
  http.get("/favicon.ico", passthrough),
  http.get("/favicon.ico", passthrough),
  http.get("https://test-sfr-covers.s3.amazonaws.com/*", passthrough),
  http.get("https://ds-header.nypl.org/*", passthrough),

  http.get(workUrl, () => {
    return HttpResponse.json(workDetailWithUp);
  }),

  http.get(fulfillUrl, ({ request }) => {
    if (!isAuthenticated(request)) {
      return new HttpResponse(null, {
        status: 401,
      });
    }
    return new HttpResponse(null, {
      status: 302,
      headers: {
        Location: "/test-download-pdf",
      },
    });
  }),

  http.get(downloadUrl, () => {
    return new HttpResponse(null, {
      status: 200,
    });
  }),

  http.get(collectionListUrl, () => {
    return HttpResponse.json(oneCollectionListData);
  }),

  http.get(invalidCollectionUrl, () => {
    return HttpResponse.json({
      status: 500,
      title: "Something went wrong",
      detail: "An unknown error occurred on the server",
    });
  }),
];

export default handlers;

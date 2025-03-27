/* eslint-disable no-empty-pattern */
import { test as base, expect } from "@playwright/test";
import { createServer, Server } from "http";
import { parse } from "url";
import { AddressInfo } from "net";
import next from "next";
import path from "path";
import { http } from "msw";

const test = base.extend<{
  setCookie(expires?: number): Promise<void>;
  port: string;
  http: typeof http;
}>({
  setCookie: [
    async ({ context }, use, _expires) => {
      async function addCookie(
        expires: number = (Date.now() + 60 * 60 * 24 * 1000) / 1000
      ) {
        const cookie = {
          name: "nyplIdentityPatron",
          value: JSON.stringify({
            token_type: "Bearer",
            access_token: "access-token",
            refresh_token: "refresh-token",
            expires: expires,
          }),
          domain: "localhost",
          path: "/",
          expires: expires,
        };
        await context.addCookies([cookie]);
      }
      addCookie();
      await use(addCookie);
    },
    { auto: true },
  ],
  port: [
    async ({}, use) => {
      const app = next({ dev: false, dir: path.resolve(__dirname, "../..") });
      await app.prepare();

      const handle = app.getRequestHandler();

      const server: Server = await new Promise((resolve) => {
        const server = createServer((req, res) => {
          const parsedUrl = parse(req.url, true);
          handle(req, res, parsedUrl);
        });

        server.listen((error) => {
          if (error) throw error;
          resolve(server);
        });
      });
      const port = String((server.address() as AddressInfo).port);
      await use(port);
    },
    { auto: true },
  ],
  http,
});

export { test, expect };

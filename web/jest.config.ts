import type { Config } from "jest";

const config: Config = {
  moduleFileExtensions: ["js", "ts", "tsx"],
  moduleNameMapper: {
    "^~(.*)$": "<rootDir>$1",
  },
  testPathIgnorePatterns: [
    "<rootDir>/.next/",
    "<rootDir>/node_modules/",
    "testUtils",
    "fixtures",
    "componentHelpers",
    "/playwright/",
  ],
  setupFilesAfterEnv: ["./jest.setup.ts"],
  resetMocks: true,
  testEnvironment: "jsdom",
};

export default config;

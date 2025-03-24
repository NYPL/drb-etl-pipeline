const path = require("path");

const nrExternals = require("newrelic/load-externals");

/**
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  webpack: (config, { isServer }) => {
    config.resolve.alias["~"] = path.resolve(__dirname);

    if (process.env.APP_ENV === "testing") {
      if (isServer) {
        config.resolve.alias = {
          ...config.resolve.alias,
          "msw/browser": false,
        };
      } else {
        // Setting `resolve.alias` to `false` will tell webpack to ignore a module.
        // `msw/node` is a server-only module that exports methods not available in
        // the `browser`.
        config.resolve.alias = {
          ...config.resolve.alias,
          "msw/node": false,
        };
      }
    }

    // In order for newrelic to effectively instrument a Next.js application,
    // the modules that newrelic supports should not be mangled by webpack. Thus,
    // we need to "externalize" all of the modules that newrelic supports.
    config = nrExternals(config);

    return config;
  },
  sassOptions: {
    includePaths: [path.join(__dirname, "styles")],
  },
  env: {
    APP_ENV: process.env.APP_ENV,
    NEW_RELIC_LICENSE_KEY: process.env.NEW_RELIC_LICENSE_KEY,
    API_URL: process.env.API_URL,
  },
  output: "standalone",
};

module.exports = nextConfig;

import { useRouter } from "next/router";
import { ParsedUrlQuery } from "querystring";
import React, { createContext, useContext, useEffect, useState } from "react";
import { extractQueryParam } from "../util/LinkUtils";

type FeatureFlag = {
  [flag: string]: boolean;
};

type FeatureFlagContextType = {
  featureFlags: FeatureFlag;
  setFeatureFlags: (featureFlags: FeatureFlag) => void;
  isFlagActive: (flag: string) => boolean;
};

export const FeatureFlagContext =
  createContext<FeatureFlagContextType>(undefined);

const extractFeatureFlagParams = (query: ParsedUrlQuery) => {
  const featureFlags = {};
  for (const param in query) {
    if (param.includes("feature_")) {
      const featureFlag = param.split("_")[1];
      featureFlags[featureFlag] = JSON.parse(extractQueryParam(query, param));
    }
  }
  return featureFlags;
};

export const FeatureFlagProvider: React.FC<{ children?: React.ReactNode }> = ({
  children,
}) => {
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag>({});
  const isFlagActive = (flag: string) => {
    return featureFlags[flag];
  };

  const router = useRouter();
  const { query } = router;

  useEffect(() => {
    const storedFeatureFlagsStr = sessionStorage.getItem("featureFlags");
    let storedFeatureFlags: FeatureFlag = {};
    if (storedFeatureFlagsStr) {
      try {
        storedFeatureFlags = JSON.parse(storedFeatureFlagsStr);
        for (const flag in storedFeatureFlags) {
          const featureFlag = "feature_" + flag;
          if (!query[featureFlag]) {
            router.push({
              query: { ...query, [featureFlag]: storedFeatureFlags[flag] },
            });
          }
        }
      } catch (e) {
        throw new Error(e);
      }
    }

    const newFeatureFlags = extractFeatureFlagParams(query);
    sessionStorage.setItem("featureFlags", JSON.stringify(newFeatureFlags));
    setFeatureFlags(newFeatureFlags);
  }, [query, router]);

  return (
    <FeatureFlagContext.Provider
      value={{
        featureFlags: featureFlags,
        setFeatureFlags: setFeatureFlags,
        isFlagActive,
      }}
    >
      {children}
    </FeatureFlagContext.Provider>
  );
};

export const useFeatureFlags = () => {
  const context = useContext(FeatureFlagContext);
  if (typeof context === "undefined") {
    throw new Error(
      "useFeatureFlags must be used within a FeatureFlagProvider"
    );
  }
  return context;
};

export default useFeatureFlags;

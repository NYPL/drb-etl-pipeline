interface Window {
  adobeDataLayer: Array<any> | undefined;
  NREUM: any;
  newrelic?: {
    noticeError(
      error: Error,
      customAttributes?: Record<string, string | number>
    );
  };
}

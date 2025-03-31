export type ApiLanguageResponse = {
  status?: number;
  data?: ApiLanguage[];
};

export type ApiLanguage = {
  language: string;
  count: number;
};

/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  readonly PUBLIC_API_URL: string;
  readonly PUBLIC_APP_NAME: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
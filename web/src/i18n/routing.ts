import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en", "bg"],
  defaultLocale: "en",
  // Keep existing URL structure — no locale prefix in paths.
  localePrefix: "never",
  // Persist the chosen locale via a cookie named NEXT_LOCALE.
  localeCookie: { name: "NEXT_LOCALE" },
});

export type Locale = (typeof routing.locales)[number];

import { cookies, headers } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { routing, type Locale } from "./routing";

const LOCALE_COOKIE_NAME = "NEXT_LOCALE";

function isSupportedLocale(value: string | null | undefined): value is Locale {
  return routing.locales.includes(value as Locale);
}

function localeFromAcceptLanguage(value: string | null): Locale {
  if (!value) {
    return routing.defaultLocale;
  }

  const requestedLanguages = value
    .split(",")
    .map((entry) => entry.trim().split(";")[0]?.toLowerCase())
    .filter((entry): entry is string => Boolean(entry));

  for (const language of requestedLanguages) {
    const exactMatch = routing.locales.find(
      (locale) => locale.toLowerCase() === language
    );

    if (exactMatch) {
      return exactMatch;
    }

    const baseLanguage = language.split("-")[0];
    const baseMatch = routing.locales.find(
      (locale) => locale.toLowerCase() === baseLanguage
    );

    if (baseMatch) {
      return baseMatch;
    }
  }

  return routing.defaultLocale;
}

export default getRequestConfig(async () => {
  const cookieStore = await cookies();
  const headerStore = await headers();

  const cookieLocale = cookieStore.get(LOCALE_COOKIE_NAME)?.value;

  const locale = isSupportedLocale(cookieLocale)
    ? cookieLocale
    : localeFromAcceptLanguage(headerStore.get("accept-language"));

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});

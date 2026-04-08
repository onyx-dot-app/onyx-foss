"use client";

import { useEffect } from "react";
import { DEFAULT_LOCALE, getCurrentLocale, setLocale } from "@/lib/i18n";

export default function LocaleSync() {
  useEffect(() => {
    setLocale(getCurrentLocale() || DEFAULT_LOCALE);
  }, []);

  return null;
}

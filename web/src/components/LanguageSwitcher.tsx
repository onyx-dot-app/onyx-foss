"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter, usePathname } from "next/navigation";
import { useTransition } from "react";
import { routing } from "@/i18n/routing";

export default function LanguageSwitcher() {
  const t = useTranslations("languageSwitcher");
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  function switchLocale(next: string) {
    // Persist choice in a cookie that the next-intl middleware reads.
    document.cookie = `NEXT_LOCALE=${next};path=/;max-age=31536000;SameSite=Lax`;
    startTransition(() => {
      router.refresh();
    });
  }

  return (
    <div className="flex items-center gap-1" aria-label={t("label")}>
      {routing.locales.map((l) => (
        <button
          key={l}
          disabled={l === locale || isPending}
          onClick={() => switchLocale(l)}
          className={
            l === locale
              ? "text-sm font-semibold text-text-900 cursor-default"
              : "text-sm text-action-link-05 hover:underline cursor-pointer disabled:opacity-50"
          }
        >
          {t(l as "en" | "bg")}
        </button>
      ))}
    </div>
  );
}

"use client";

import React from "react";
import { useSettings } from "@/lib/settings/hooks";
import Text from "@/refresh-components/texts/Text";
import { useTranslations } from "next-intl";

export default function LoginText() {
  const { appName } = useSettings();
  const t = useTranslations("auth.login");
  return (
    <div className="w-full flex flex-col ">
      <Text as="p" headingH2 text05>
        {t("title", { appName })}
      </Text>
      <Text as="p" text03 mainUiMuted>
        {t("subtitle")}
      </Text>
    </div>
  );
}

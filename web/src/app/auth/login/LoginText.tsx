"use client";

import React, { useContext } from "react";
import { SettingsContext } from "@/providers/SettingsProvider";
import Text from "@/refresh-components/texts/Text";
import { t } from "@/lib/i18n";

export default function LoginText() {
  const settings = useContext(SettingsContext);
  const appName =
    (settings && settings?.enterpriseSettings?.application_name) || "Onyx";

  return (
    <div className="w-full flex flex-col ">
      <Text as="p" headingH2 text05>
        {t("auth.welcomeTo", { appName })}
      </Text>
      <Text as="p" text03 mainUiMuted>
        {t("auth.subtitle")}
      </Text>
    </div>
  );
}

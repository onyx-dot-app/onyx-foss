"use client";

import { useState } from "react";
import InputSelect from "@/refresh-components/inputs/InputSelect";
import { Label } from "@/components/Field";
import { useTranslations } from "next-intl";

interface ReferralSourceSelectorProps {
  defaultValue?: string;
}

export default function ReferralSourceSelector({
  defaultValue,
}: ReferralSourceSelectorProps) {
  const [referralSource, setReferralSource] = useState(defaultValue);
  const t = useTranslations("auth.referralSource");

  const referralOptions = [
    { value: "search", label: t("options.search") },
    { value: "friend", label: t("options.friend") },
    { value: "linkedin", label: t("options.linkedin") },
    { value: "twitter", label: t("options.twitter") },
    { value: "hackernews", label: t("options.hackernews") },
    { value: "reddit", label: t("options.reddit") },
    { value: "youtube", label: t("options.youtube") },
    { value: "podcast", label: t("options.podcast") },
    { value: "blog", label: t("options.blog") },
    { value: "ads", label: t("options.ads") },
    { value: "other", label: t("options.other") },
  ];

  const handleChange = (value: string) => {
    setReferralSource(value);
    const cookies = require("js-cookie");
    cookies.set("referral_source", value, {
      expires: 365,
      path: "/",
      sameSite: "strict",
    });
  };

  return (
    <div className="w-full gap-y-2 flex flex-col">
      <Label className="text-text-950" small={false}>
        {t("label")}
      </Label>
      <InputSelect value={referralSource} onValueChange={handleChange}>
        <InputSelect.Trigger placeholder={t("placeholder")} />

        <InputSelect.Content>
          {referralOptions.map((option) => (
            <InputSelect.Item key={option.value} value={option.value}>
              {option.label}
            </InputSelect.Item>
          ))}
        </InputSelect.Content>
      </InputSelect>
    </div>
  );
}

"use client";

import { toast } from "@opal/layouts";
import { requestEmailVerification } from "../lib";
import { Spinner } from "@/components/Spinner";
import { useState, JSX } from "react";
import { useTranslations } from "next-intl";

export function RequestNewVerificationEmail({
  children,
  email,
}: {
  children: JSX.Element | string;
  email: string;
}) {
  const [isRequestingVerification, setIsRequestingVerification] =
    useState(false);
  const t = useTranslations("auth.waitingOnVerification");

  return (
    <button
      className="text-link"
      onClick={async () => {
        setIsRequestingVerification(true);
        const response = await requestEmailVerification(email);
        setIsRequestingVerification(false);

        if (response.ok) {
          toast.success(t("newEmailSent"));
        } else {
          const errorDetail = (await response.json()).detail;
          toast.error(t("failedToSend", { errorDetail }));
        }
      }}
    >
      {isRequestingVerification && <Spinner />}
      {children}
    </button>
  );
}

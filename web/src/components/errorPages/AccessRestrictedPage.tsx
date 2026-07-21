"use client";

import { useState } from "react";
import Link from "next/link";
import ErrorPageLayout from "@/components/errorPages/ErrorPageLayout";
import { Button } from "@opal/components";
import InlineExternalLink from "@/refresh-components/InlineExternalLink";
import { logout } from "@/lib/users/svc";
import { NEXT_PUBLIC_CLOUD_ENABLED } from "@/lib/constants";
import { useLicense } from "@/hooks/useLicense";
import { useSettings } from "@/lib/settings/hooks";
import { ApplicationStatus } from "@/lib/settings/types";
import Text from "@/refresh-components/texts/Text";
import { SvgLock } from "@opal/icons";
import { useTranslations } from "next-intl";

const linkClassName = "text-action-link-05 hover:text-action-link-06 underline";

interface ResubscriptionSessionResponse {
  sessionId: string | null;
  url: string | null;
  requires_payment_method_update: boolean;
}

const fetchResubscriptionSession =
  async (): Promise<ResubscriptionSessionResponse> => {
    const response = await fetch("/api/tenants/create-subscription-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      throw new Error("Failed to create resubscription session");
    }
    return response.json();
  };

export default function AccessRestricted() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: license } = useLicense();
  const settings = useSettings();
  const t = useTranslations("accessRestricted");

  const isSeatLimitExceeded =
    settings.application_status === ApplicationStatus.SEAT_LIMIT_EXCEEDED;
  const hadPreviousLicense = license?.has_license === true;
  const showRenewalMessage = NEXT_PUBLIC_CLOUD_ENABLED || hadPreviousLicense;

  function getSeatLimitMessage() {
    const { used_seats, seat_count } = settings;
    const counts =
      used_seats != null && seat_count != null
        ? ` (${used_seats} users / ${seat_count} seats)`
        : "";
    return t("seatLimitExceeded", { counts });
  }

  const initialModalMessage = isSeatLimitExceeded
    ? getSeatLimitMessage()
    : showRenewalMessage
      ? NEXT_PUBLIC_CLOUD_ENABLED
        ? t("cloudSuspended")
        : t("licenseSuspended")
      : t("noLicense");

  const handleResubscribe = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // `url` covers both the new-checkout and past_due payment-update responses.
      const { url } = await fetchResubscriptionSession();
      if (!url) {
        throw new Error("No redirect URL returned");
      }
      window.location.href = url;
    } catch (error) {
      console.error("Error creating resubscription session:", error);
      setError(t("errorResubscription"));
      setIsLoading(false);
    }
  };

  return (
    <ErrorPageLayout>
      <div className="flex items-center gap-2">
        <Text headingH2>{t("title")}</Text>
        <SvgLock className="stroke-status-error-05 w-6 h-6" />
      </div>

      <Text text03>{initialModalMessage}</Text>

      {isSeatLimitExceeded ? (
        <>
          <Text text03>
            {t("manageUsers")}{" "}
            <Link className={linkClassName} href="/admin/users">
              {t("userManagement")}
            </Link>{" "}
            {t("upgradeOrReduce")}{" "}
            <Link className={linkClassName} href="/admin/billing">
              {t("adminBilling")}
            </Link>{" "}
            {t("billingPage")}
          </Text>

          <div className="flex flex-row gap-2">
            <Button
              onClick={async () => {
                await logout();
                window.location.reload();
              }}
            >
              {t("logOut")}
            </Button>
          </div>
        </>
      ) : NEXT_PUBLIC_CLOUD_ENABLED ? (
        <>
          <Text text03>{t("updatePayment")}</Text>

          <Text text03>{t("adminResubscribe")}</Text>

          <div className="flex flex-row gap-2">
            <Button disabled={isLoading} onClick={handleResubscribe}>
              {isLoading ? t("loading") : t("resubscribe")}
            </Button>
            <Button
              prominence="secondary"
              onClick={async () => {
                await logout();
                window.location.reload();
              }}
            >
              {t("logOut")}
            </Button>
          </div>

          {error && <Text className="text-status-error-05">{error}</Text>}
        </>
      ) : (
        <>
          <Text text03>
            {hadPreviousLicense ? t("renewLicense") : t("getStartedLicense")}
          </Text>

          <Text text03>
            {t("adminBillingLink")}{" "}
            <Link className={linkClassName} href="/admin/billing">
              {t("adminBillingPage")}
            </Link>{" "}
            {hadPreviousLicense ? t("renewPage") : t("activatePage")}{" "}
            <a className={linkClassName} href="mailto:support@onyx.app">
              support@onyx.app
            </a>{" "}
            {t("billingAssistance")}
          </Text>

          <div className="flex flex-row gap-2">
            <Button
              onClick={async () => {
                await logout();
                window.location.reload();
              }}
            >
              {t("logOut")}
            </Button>
          </div>
        </>
      )}

      <Text text03>
        {t("needHelp")}{" "}
        <InlineExternalLink
          className={linkClassName}
          href="https://discord.gg/4NA5SbzrWb"
        >
          {t("discordCommunity")}
        </InlineExternalLink>{" "}
        {t("forSupport")}
      </Text>
    </ErrorPageLayout>
  );
}

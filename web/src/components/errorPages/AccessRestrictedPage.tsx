"use client";

import Link from "next/link";
import ErrorPageLayout from "@/components/errorPages/ErrorPageLayout";
import { Button } from "@opal/components";
import InlineExternalLink from "@/refresh-components/InlineExternalLink";
import { logout } from "@/lib/users/svc";
import { useSettings } from "@/lib/settings/hooks";
import { ApplicationStatus } from "@/lib/settings/types";
import Text from "@/refresh-components/texts/Text";
import { SvgLock } from "@opal/icons";
import { useTranslations } from "next-intl";

const linkClassName = "text-action-link-05 hover:text-action-link-06 underline";

export default function AccessRestricted() {
  const settings = useSettings();
  const t = useTranslations("accessRestricted");

  const isSeatLimitExceeded =
    settings.application_status === ApplicationStatus.SEAT_LIMIT_EXCEEDED;

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
    : "Access to this section is currently restricted by an administrator policy.";

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
                window.location.reload();
              }}
            >
              {t("logOut")}
          </div>

          {error && <Text className="text-status-error-05">{error}</Text>}
        </>
      ) : (
        <>
>>>>>>> f3021f36f (feat: default enterprise access and remove subscription gating)
          </Text>

          <Text text03>
            {t("adminBillingLink")}{" "}
              {t("adminBillingPage")}
            </Link>{" "}
<<<<<<< HEAD
            {hadPreviousLicense ? t("renewPage") : t("activatePage")}{" "}
            <a className={linkClassName} href="mailto:support@onyx.app">
              support@onyx.app
            </a>{" "}
            {t("billingAssistance")}
=======
            page for deployment and access details, or reach out to{" "}
            <a className={linkClassName} href="mailto:support@onyx.app">
              support@onyx.app
            </a>{" "}
            for assistance.
>>>>>>> f3021f36f (feat: default enterprise access and remove subscription gating)
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

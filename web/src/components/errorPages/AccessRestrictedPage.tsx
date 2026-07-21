"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@opal/components";
import { SvgLock } from "@opal/icons";

import ErrorPageLayout from "@/components/errorPages/ErrorPageLayout";
import { ApplicationStatus } from "@/lib/settings/types";
import { useSettings } from "@/lib/settings/hooks";
import { logout } from "@/lib/users/svc";
import InlineExternalLink from "@/refresh-components/InlineExternalLink";
import Text from "@/refresh-components/texts/Text";

const linkClassName = "text-action-link-05 hover:text-action-link-06 underline";

export default function AccessRestricted() {
  const settings = useSettings();
  const t = useTranslations("accessRestricted");

  const isSeatLimitExceeded =
    settings.application_status === ApplicationStatus.SEAT_LIMIT_EXCEEDED;

  const seatLimitMessage = () => {
    const { used_seats, seat_count } = settings;

    const counts =
      used_seats != null && seat_count != null
        ? ` (${used_seats} users / ${seat_count} seats)`
        : "";

    return t("seatLimitExceeded", { counts });
  };

  const handleLogout = async () => {
    await logout();
    window.location.reload();
  };

  return (
    <ErrorPageLayout>
      <div className="flex items-center gap-2">
        <Text headingH2>{t("title")}</Text>
        <SvgLock className="stroke-status-error-05 h-6 w-6" />
      </div>

      <Text text03>
        {isSeatLimitExceeded ? seatLimitMessage() : t("adminPolicyRestricted")}
      </Text>

      {isSeatLimitExceeded ? (
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
      ) : (
        <Text text03>
          {t("adminBillingLink")}{" "}
          <Link className={linkClassName} href="/admin/billing">
            {t("adminBillingPage")}
          </Link>{" "}
          {t("deploymentDetails")}
        </Text>
      )}

      <div className="flex flex-row gap-2">
        <Button onClick={handleLogout}>{t("logOut")}</Button>
      </div>

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

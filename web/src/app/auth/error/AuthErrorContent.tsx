"use client";

import AuthFlowContainer from "@/components/auth/AuthFlowContainer";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";

import { NEXT_PUBLIC_CLOUD_ENABLED } from "@/lib/constants";
import { useTranslations } from "next-intl";

type ErrorCodeKey =
  | "access_denied"
  | "login_required"
  | "consent_required"
  | "interaction_required"
  | "invalid_scope"
  | "server_error"
  | "temporarily_unavailable";

const KNOWN_ERROR_CODES: ErrorCodeKey[] = [
  "access_denied",
  "login_required",
  "consent_required",
  "interaction_required",
  "invalid_scope",
  "server_error",
  "temporarily_unavailable",
];

interface AuthErrorContentProps {
  message: string | null;
}

function AuthErrorContent({ message: rawMessage }: AuthErrorContentProps) {
  const t = useTranslations("auth.error");

  function resolveMessage(raw: string | null): string | null {
    if (!raw) return null;
    if (KNOWN_ERROR_CODES.includes(raw as ErrorCodeKey)) {
      return t(`errorCodes.${raw as ErrorCodeKey}`);
    }
    return raw;
  }

  const message = resolveMessage(rawMessage);

  return (
    <AuthFlowContainer>
      <div className="flex flex-col items-center gap-4">
        <Text headingH2 text05>
          {t("title")}
        </Text>
        <Text mainContentBody text03>
          {t("subtitle")}
        </Text>
        {/* TODO: Error card component */}
        <div className="w-full rounded-12 border border-status-error-05 bg-status-error-00 p-4">
          {message ? (
            <Text mainContentBody className="text-status-error-05">
              {message}
            </Text>
          ) : (
            <div className="flex flex-col gap-2 px-4">
              <Text mainContentEmphasis className="text-status-error-05">
                {t("possibleIssues")}
              </Text>
              <Text as="li" mainContentBody className="text-status-error-05">
                {t("incorrectCredentials")}
              </Text>
              <Text as="li" mainContentBody className="text-status-error-05">
                {t("systemDisruption")}
              </Text>
              <Text as="li" mainContentBody className="text-status-error-05">
                {t("accessRestrictions")}
              </Text>
            </div>
          )}
        </div>

        <Button href="/auth/login" width="full">
          {t("returnToLogin")}
        </Button>

        <Text mainContentBody text04>
          {NEXT_PUBLIC_CLOUD_ENABLED ? (
            <>
              {t("contactCloud")}{" "}
              <a href="mailto:support@onyx.app" className="text-action-link-05">
                support@onyx.app
              </a>
            </>
          ) : (
            t("contactAdmin")
          )}
        </Text>
      </div>
    </AuthFlowContainer>
  );
}

export default AuthErrorContent;

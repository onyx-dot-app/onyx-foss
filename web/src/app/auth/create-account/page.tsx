"use client";

import AuthFlowContainer from "@/components/auth/AuthFlowContainer";
import { REGISTRATION_URL } from "@/lib/constants";
import { Button } from "@opal/components";
import Link from "next/link";
import { SvgImport } from "@opal/icons";
import { t } from "@/lib/i18n";

export default function Page() {
  return (
    <AuthFlowContainer>
      <div className="flex flex-col space-y-6">
        <h2 className="text-2xl font-bold text-text-900 text-center">
          {t("auth.accountNotFound")}
        </h2>
        <p className="text-text-700 max-w-md text-center">
          {t("auth.accountNotFoundBody")}
        </p>
        <ul className="list-disc text-left text-text-600 w-full pl-6 mx-auto">
          <li>{t("auth.beInvited")}</li>
          <li>{t("auth.createNewTeam")}</li>
        </ul>
        <div className="flex justify-center">
          <Button
            href={`${REGISTRATION_URL}/register`}
            width="full"
            icon={SvgImport}
          >
            {t("auth.createNewOrganization")}
          </Button>
        </div>
        <p className="text-sm text-text-500 text-center">
          {t("auth.differentEmail")}{" "}
          <Link
            href="/auth/login"
            className="text-action-link-05 hover:underline"
          >
            {t("auth.signIn")}
          </Link>
        </p>
      </div>
    </AuthFlowContainer>
  );
}

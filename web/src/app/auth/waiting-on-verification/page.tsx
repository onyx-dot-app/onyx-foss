import { getCurrentUserSS } from "@/lib/users/svcSS";
import { getAuthTypeMetadataSS } from "@/lib/auth/svcSS";
import { AuthTypeMetadata } from "@/lib/auth/types";
import { redirect } from "next/navigation";
import { User } from "@/lib/types";
import { RequestNewVerificationEmail } from "./RequestNewVerificationEmail";
import { Logo } from "@/lib/app/components";
import { Text } from "@opal/components";
import { markdown } from "@opal/utils";
import { getTranslations } from "next-intl/server";

export default async function Page() {
  // catch cases where the backend is completely unreachable here
  // without try / catch, will just raise an exception and the page
  // will not render
  let authTypeMetadata: AuthTypeMetadata | null = null;
  let currentUser: User | null = null;
  try {
    [authTypeMetadata, currentUser] = await Promise.all([
      getAuthTypeMetadataSS(),
      getCurrentUserSS(),
    ]);
  } catch (e) {
    console.log(`Some fetch failed for the login page - ${e}`);
  }

  if (!currentUser) {
    return redirect("/auth/login");
  }

  if (!authTypeMetadata?.requiresVerification || currentUser.is_verified) {
    return redirect("/app");
  }

  const t = await getTranslations("auth.waitingOnVerification");

  return (
    <main>
      <div className="min-h-screen flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8 gap-4">
        <Logo folded size={64} className="mx-auto w-fit" />
        <div className="flex flex-col gap-2">
          <Text as="span">
            {markdown(t("notVerifiedMessage", { email: currentUser.email }))}
          </Text>
          <div className="flex flex-row items-center gap-1">
            <Text as="span">{t("noEmail")}</Text>
            <RequestNewVerificationEmail email={currentUser.email}>
              <Text as="span">{t("requestNew")}</Text>
            </RequestNewVerificationEmail>
            <Text as="span">{t("toRequestNew")}</Text>
          </div>
        </div>
      </div>
    </main>
  );
}

"use client";

import { SettingsLayouts } from "@opal/layouts";
import { Section } from "@/layouts/general-layouts";
import Text from "@/refresh-components/texts/Text";
import { MessageCard, LinkButton } from "@opal/components";
import { SvgWallet, SvgOrganization } from "@opal/icons";

import "./billing.css";

const SUPPORT_EMAIL = "support@onyx.app";

export default function BillingPage() {
  const billingHelpHref = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
    "[Billing] enterprise access"
  )}`;

  return (
    <SettingsLayouts.Root>
      <SettingsLayouts.Header
        icon={SvgWallet}
        title="Plans & Billing"
        divider
      />
      <SettingsLayouts.Body>
        <Section gap={1} width="full" height="auto">
          <MessageCard
            variant="success"
            title="Enterprise plan is enabled by default"
            description="All users have full access. Subscription and license activation are not required in this deployment."
          />

          <div className="w-full rounded-border border border-border-subtle-04 bg-background-200 p-6">
            <Section
              flexDirection="row"
              alignItems="start"
              justifyContent="between"
              width="full"
              height="auto"
            >
              <Section gap={0.25} alignItems="start" width="fit" height="auto">
                <SvgOrganization className="h-5 w-5" />
                <Text headingH3 text04>
                  Enterprise Access
                </Text>
                <Text secondaryBody text03>
                  Your workspace is operating with enterprise capabilities for
                  all users.
                </Text>
              </Section>
              <LinkButton href={billingHelpHref}>Billing Help</LinkButton>
            </Section>
          </div>
        </Section>
      </SettingsLayouts.Body>
    </SettingsLayouts.Root>
  );
}

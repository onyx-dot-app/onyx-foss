"use client";

import { Logo } from "@/lib/app/components";
import AgentAvatar from "@/refresh-components/avatars/AgentAvatar";
import Text from "@/refresh-components/texts/Text";
import { MinimalAgent } from "@/lib/agents/types";
import { useState, useEffect } from "react";
import { useSettings } from "@/lib/settings/hooks";
import FrostedDiv from "@/refresh-components/FrostedDiv";
import { Section } from "@/layouts/general-layouts";
import { useTranslations } from "next-intl";

export interface WelcomeMessageProps {
  agent?: MinimalAgent;
  isDefaultAgent: boolean;
}

export default function WelcomeMessage({
  agent,
  isDefaultAgent,
}: WelcomeMessageProps) {
  const t = useTranslations("welcomeMessage");
  const settings = useSettings();
  const greetings = t.raw("greetings") as string[];

  // Use a stable default for SSR, then randomize on client after hydration
  const [greeting, setGreeting] = useState(greetings[0]);

  useEffect(() => {
    if (settings.enterprise?.custom_greeting_message) {
      setGreeting(settings.enterprise.custom_greeting_message);
    } else {
      setGreeting(greetings[Math.floor(Math.random() * greetings.length)] as string);
    }
  }, [settings.enterprise?.custom_greeting_message]);

  let content: React.ReactNode = null;

  if (isDefaultAgent) {
    content = (
      <Section
        data-testid="onyx-logo"
        flexDirection="column"
        alignItems="start"
        gap={0.5}
        width="fit"
      >
        <Logo folded size={32} />
        <Text as="p" headingH2>
          {greeting}
        </Text>
      </Section>
    );
  } else if (agent) {
    content = (
      <Section
        data-testid="agent-name-display"
        flexDirection="column"
        alignItems="start"
        gap={0.5}
        width="fit"
      >
        <AgentAvatar agent={agent} size={36} />
        <Text as="p" headingH2>
          {agent.name}
        </Text>
      </Section>
    );
  }

  // if we aren't using the default agent, we need to wait for the agent info to load
  // before rendering
  if (!content) return null;

  return (
    <FrostedDiv
      data-testid="chat-intro"
      className="flex flex-col items-center justify-center gap-3 w-full max-w-(--app-page-main-content-width)"
    >
      {content}
    </FrostedDiv>
  );
}

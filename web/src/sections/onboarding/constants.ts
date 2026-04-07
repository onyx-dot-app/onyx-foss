import { OnboardingStep, FinalStepItemProps } from "@/interfaces/onboarding";
import { SvgGlobe, SvgImage, SvgUsers } from "@opal/icons";
import { t } from "@/lib/i18n";

type StepConfig = {
  index: number;
  title: string;
  buttonText: string;
  iconPercentage: number;
};

export const STEP_CONFIG: Record<OnboardingStep, StepConfig> = {
  [OnboardingStep.Welcome]: {
    index: 0,
    title: t("onboarding.setupIntro"),
    buttonText: t("onboarding.letsGo"),
    iconPercentage: 10,
  },
  [OnboardingStep.Name]: {
    index: 1,
    title: t("onboarding.setupIntro"),
    buttonText: t("onboarding.next"),
    iconPercentage: 40,
  },
  [OnboardingStep.LlmSetup]: {
    index: 2,
    title: t("onboarding.connectModelsIntro"),
    buttonText: t("onboarding.next"),
    iconPercentage: 70,
  },
  [OnboardingStep.Complete]: {
    index: 3,
    title: t("onboarding.finishIntro"),
    buttonText: t("onboarding.finishSetup"),
    iconPercentage: 100,
  },
} as const;

export const TOTAL_STEPS = 3;

export const STEP_NAVIGATION: Record<
  OnboardingStep,
  { next?: OnboardingStep; prev?: OnboardingStep }
> = {
  [OnboardingStep.Welcome]: { next: OnboardingStep.Name },
  [OnboardingStep.Name]: {
    next: OnboardingStep.LlmSetup,
    prev: OnboardingStep.Welcome,
  },
  [OnboardingStep.LlmSetup]: {
    next: OnboardingStep.Complete,
    prev: OnboardingStep.Name,
  },
  [OnboardingStep.Complete]: { prev: OnboardingStep.LlmSetup },
};

export const FINAL_SETUP_CONFIG: FinalStepItemProps[] = [
  {
    title: t("onboarding.selectWebSearchProvider"),
    description: t("onboarding.webSearchDescription"),
    icon: SvgGlobe,
    buttonText: t("onboarding.webSearchCta"),
    buttonHref: "/admin/configuration/web-search",
  },
  {
    title: t("onboarding.enableImageGeneration"),
    description: t("onboarding.imageGenerationDescription"),
    icon: SvgImage,
    buttonText: t("onboarding.imageGenerationCta"),
    buttonHref: "/admin/configuration/image-generation",
  },
  {
    title: t("onboarding.inviteYourTeam"),
    description: t("onboarding.inviteTeamDescription"),
    icon: SvgUsers,
    buttonText: t("onboarding.manageUsers"),
    buttonHref: "/admin/users",
  },
];

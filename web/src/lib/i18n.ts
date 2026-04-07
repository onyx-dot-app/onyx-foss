export type Locale = "en" | "ja";

export const DEFAULT_LOCALE: Locale = "ja";

type TranslationValue = string | TranslationDictionary;
type TranslationDictionary = {
  [key: string]: TranslationValue;
};

const dictionaries: Record<Locale, TranslationDictionary> = {
  en: {
    auth: {
      welcomeTo: "Welcome to {appName}",
      subtitle: "Your open source AI platform for work",
      emailVerified: "Your email has been verified! Please sign in to continue.",
      resetPassword: "Reset Password",
      noAccount: "Don't have an account?",
      createAccountLink: "Create an account",
      completeSignup: "Complete your sign up",
      createAccountTitle: "Create account",
      getStarted: "Get started with Onyx",
      emailAddress: "Email Address",
      password: "Password",
      emailPlaceholder: "email@yourcompany.com",
      join: "Join",
      createAccount: "Create Account",
      signIn: "Sign In",
      continueAsGuest: "or continue as guest",
      joining: "Joining...",
      creatingAccount: "Creating account...",
      signingIn: "Signing in...",
      accountCreatedSigningIn: "Account created. Signing in...",
      signedInSuccessfully: "Signed in successfully.",
      passwordMinLength: "Password must be at least {count} characters",
      unknownError: "Unknown error",
      accountAlreadyExists:
        "An account already exists with the specified email.",
      tooManyRequests: "Too many requests. Please try again later.",
      failedToSignup: "Failed to sign up - {message}",
      accountCreatedPleaseLogin: "Account created successfully. Please log in.",
      invalidEmailOrPassword: "Invalid email or password",
      createAccountToSetPassword: "Create an account to set a password",
      failedToLogin: "Failed to login - {message}",
      continueWithGoogle: "Continue with Google",
      continueWithOidc: "Continue with OIDC SSO",
      continueWithSaml: "Continue with SAML SSO",
      accountNotFound: "Account Not Found",
      accountNotFoundBody:
        "We couldn't find your account in our records. To access Onyx, you need to either:",
      beInvited: "Be invited to an existing Onyx team",
      createNewTeam: "Create a new Onyx team",
      createNewOrganization: "Create New Organization",
      differentEmail: "Have an account with a different email?",
      forgotPassword: "Forgot Password",
      passwordResetEmailSent:
        "Password reset email sent. Please check your inbox.",
      genericError: "An error occurred. Please try again.",
      emailLabel: "Email",
      backToLogin: "Back to Login",
      alreadyHaveAccount: "Already have an account?",
      cloudOrDivider: "or",
      createAccountCta: "Create an Account",
      signInCta: "Sign In",
    },
    onboarding: {
      setupIntro: "Let's take a moment to get you set up.",
      letsGo: "Let's Go",
      next: "Next",
      connectModelsIntro: "Almost there! Connect your models to start chatting.",
      finishIntro:
        "You're all set, review the optional settings or click Finish Setup",
      finishSetup: "Finish Setup",
      selectWebSearchProvider: "Select web search provider",
      webSearchDescription:
        "Enable Onyx to search the internet for information.",
      webSearchCta: "Web Search",
      enableImageGeneration: "Enable image generation",
      imageGenerationDescription:
        "Set up models to create images in your chats.",
      imageGenerationCta: "Image Generation",
      inviteYourTeam: "Invite your team",
      inviteTeamDescription: "Manage users and permissions for your team",
      manageUsers: "Manage Users",
      whatShouldOnyxCallYou: "What should Onyx call you?",
      displayNameDescription: "We will display this name in the app.",
      yourName: "Your name",
      connectLlmModels: "Connect your LLM models",
      llmSupportDescription:
        "Onyx supports both self-hosted models and popular providers.",
      viewInAdminPanel: "View in Admin Panel",
      customLlmProvider: "Custom LLM Provider",
      liteLlmCompatibleApis: "LiteLLM Compatible APIs",
      modelsConnected: "{count} models connected",
      connected: "connected",
      model: "model",
      models: "models",
      stepOf: "Step {current} of {total}",
      allSet: "You're all set!",
      saveNameFailed: "Failed to save name. Please try again.",
    },
    common: {
      edit: "Edit",
      save: "Save",
      or: "or",
      connect: "Connect",
      share: "Share",
      rename: "Rename",
      delete: "Delete",
      project: "Project",
      selectDate: "Select Date",
      today: "Today",
      selectTimeRange: "Select a time range",
    },
    app: {
      authenticationSuccessful: "Authentication successful",
      fileFailedRemoved: "File failed and was removed: {names}",
      filesFailedRemoved: "Files failed and were removed: {names}",
      noPreviousMessageFound: "No previously-submitted user message found.",
      sources: "Sources",
      chatNotFound: "Chat not found",
      accessDenied: "Access denied",
      somethingWentWrong: "Something went wrong",
      chatSessionMissing:
        "This chat session doesn't exist or has been deleted.",
      chatSessionForbidden:
        "You don't have permission to view this chat session.",
      startNewChat: "Start a new chat",
      attachFiles: "Attach Files",
      readingTab: "Reading tab...",
      readThisTab: "Read this tab",
      deepResearch: "Deep Research",
      setupVoice: "Set up voice",
      voiceNotConfigured: "Voice not configured. Set up in admin settings.",
      listening: "Listening...",
      onyxSpeaking: "Onyx is speaking...",
      searchConnectedSources: "Search connected sources",
      howCanIHelp: "How can I help you today?",
      createNewPrompt: "Create New Prompt",
      sharedInputPrompt: "How can Onyx help you today",
      startNewSession: "Start New Session",
    },
    sidebar: {
      failedToLogout: "Failed to logout",
      userSettings: "User Settings",
      notifications: "Notifications",
      helpFaq: "Help & FAQ",
      logIn: "Log in",
      logOut: "Log out",
      noNotifications: "No notifications",
      dismiss: "Dismiss",
      searchProjects: "Search Projects",
      moveToProject: "Move to Project",
      removeFromProject: "Remove from {projectName}",
      deleteChatTitle: "Delete Chat",
      deleteChatConfirmation:
        "Are you sure you want to delete this chat? This action cannot be undone.",
      createProject: "Create {projectName}",
      failedToDeleteChat: "Failed to delete chat. Please try again.",
      failedToCreateProject: "Failed to create project. Please try again.",
    },
    time: {
      second: "second",
      minute: "minute",
      hour: "hour",
      day: "day",
      week: "week",
      month: "month",
      year: "year",
      ago: "{count} {unit} ago",
      today: "Today",
      yesterday: "Yesterday",
    },
  },
  ja: {
    auth: {
      welcomeTo: "{appName}へようこそ",
      subtitle: "仕事のためのオープンソースAIプラットフォーム",
      emailVerified: "メール認証が完了しました。続行するにはログインしてください。",
      resetPassword: "パスワードをリセット",
      noAccount: "アカウントをお持ちでないですか？",
      createAccountLink: "アカウントを作成",
      completeSignup: "サインアップを完了",
      createAccountTitle: "アカウントを作成",
      getStarted: "Onyx を使い始めましょう",
      emailAddress: "メールアドレス",
      password: "パスワード",
      emailPlaceholder: "email@yourcompany.com",
      join: "参加する",
      createAccount: "アカウントを作成",
      signIn: "ログイン",
      continueAsGuest: "またはゲストとして続行",
      joining: "参加処理中...",
      creatingAccount: "アカウント作成中...",
      signingIn: "ログイン中...",
      accountCreatedSigningIn: "アカウントを作成しました。ログインしています...",
      signedInSuccessfully: "ログインしました。",
      passwordMinLength: "パスワードは{count}文字以上で入力してください",
      unknownError: "不明なエラー",
      accountAlreadyExists:
        "指定したメールアドレスのアカウントはすでに存在します。",
      tooManyRequests:
        "リクエストが多すぎます。しばらくしてから再度お試しください。",
      failedToSignup: "サインアップに失敗しました: {message}",
      accountCreatedPleaseLogin:
        "アカウントを作成しました。ログインしてください。",
      invalidEmailOrPassword:
        "メールアドレスまたはパスワードが正しくありません",
      createAccountToSetPassword:
        "パスワードを設定するにはアカウントを作成してください",
      failedToLogin: "ログインに失敗しました: {message}",
      continueWithGoogle: "Googleで続行",
      continueWithOidc: "OIDC SSOで続行",
      continueWithSaml: "SAML SSOで続行",
      accountNotFound: "アカウントが見つかりません",
      accountNotFoundBody:
        "登録情報の中にアカウントが見つかりませんでした。Onyx を利用するには、次のいずれかが必要です。",
      beInvited: "既存の Onyx チームに招待される",
      createNewTeam: "新しい Onyx チームを作成する",
      createNewOrganization: "新しい組織を作成",
      differentEmail: "別のメールアドレスでアカウントをお持ちですか？",
      forgotPassword: "パスワードをお忘れですか",
      passwordResetEmailSent:
        "パスワード再設定メールを送信しました。受信トレイを確認してください。",
      genericError:
        "エラーが発生しました。しばらくしてから再度お試しください。",
      emailLabel: "メールアドレス",
      backToLogin: "ログインに戻る",
      alreadyHaveAccount: "すでにアカウントをお持ちですか？",
      cloudOrDivider: "または",
      createAccountCta: "アカウントを作成",
      signInCta: "ログイン",
    },
    onboarding: {
      setupIntro: "セットアップを進めましょう。",
      letsGo: "はじめる",
      next: "次へ",
      connectModelsIntro:
        "あと少しです。チャットを始めるためにモデルを接続してください。",
      finishIntro:
        "準備が整いました。任意の設定を確認するか、セットアップを完了してください。",
      finishSetup: "セットアップを完了",
      selectWebSearchProvider: "Web検索プロバイダを選択",
      webSearchDescription:
        "Onyx がインターネット上の情報を検索できるようにします。",
      webSearchCta: "Web検索",
      enableImageGeneration: "画像生成を有効化",
      imageGenerationDescription:
        "チャットで画像を作成するためのモデルを設定します。",
      imageGenerationCta: "画像生成",
      inviteYourTeam: "チームを招待",
      inviteTeamDescription: "チームのユーザーと権限を管理します",
      manageUsers: "ユーザー管理",
      whatShouldOnyxCallYou: "Onyx での表示名を入力してください",
      displayNameDescription: "この名前がアプリ内に表示されます。",
      yourName: "お名前",
      connectLlmModels: "LLMモデルを接続",
      llmSupportDescription:
        "Onyx はセルフホストモデルと主要プロバイダの両方に対応しています。",
      viewInAdminPanel: "管理画面で見る",
      customLlmProvider: "カスタム LLM プロバイダ",
      liteLlmCompatibleApis: "LiteLLM 互換 API",
      modelsConnected: "{count}件のモデルを接続済み",
      connected: "接続済み",
      model: "モデル",
      models: "モデル",
      stepOf: "ステップ {current} / {total}",
      allSet: "準備完了です",
      saveNameFailed: "名前の保存に失敗しました。もう一度お試しください。",
    },
    common: {
      edit: "編集",
      save: "保存",
      or: "または",
      connect: "接続",
      share: "共有",
      rename: "名前を変更",
      delete: "削除",
      project: "プロジェクト",
      selectDate: "日付を選択",
      today: "今日",
      selectTimeRange: "期間を選択",
    },
    app: {
      authenticationSuccessful: "認証が完了しました",
      fileFailedRemoved: "ファイルの処理に失敗したため削除しました: {names}",
      filesFailedRemoved:
        "ファイルの処理に失敗したため削除しました: {names}",
      noPreviousMessageFound: "再送できる直前のユーザーメッセージが見つかりません。",
      sources: "ソース",
      chatNotFound: "チャットが見つかりません",
      accessDenied: "アクセス権がありません",
      somethingWentWrong: "問題が発生しました",
      chatSessionMissing:
        "このチャットセッションは存在しないか、削除されています。",
      chatSessionForbidden:
        "このチャットセッションを表示する権限がありません。",
      startNewChat: "新しいチャットを開始",
      attachFiles: "ファイルを添付",
      readingTab: "タブを読み込み中...",
      readThisTab: "このタブを読む",
      deepResearch: "詳細リサーチ",
      setupVoice: "音声設定",
      voiceNotConfigured: "音声機能は未設定です。管理画面で設定してください。",
      listening: "音声を聞いています...",
      onyxSpeaking: "Onyx が話しています...",
      searchConnectedSources: "接続済みソースを検索",
      howCanIHelp: "今日は何をお手伝いできますか？",
      createNewPrompt: "新しいプロンプトを作成",
      sharedInputPrompt: "Onyx に何を手伝ってほしいですか",
      startNewSession: "新しいセッションを開始",
    },
    sidebar: {
      failedToLogout: "ログアウトに失敗しました",
      userSettings: "ユーザー設定",
      notifications: "通知",
      helpFaq: "ヘルプ・FAQ",
      logIn: "ログイン",
      logOut: "ログアウト",
      noNotifications: "通知はありません",
      dismiss: "閉じる",
      searchProjects: "プロジェクトを検索",
      moveToProject: "プロジェクトへ移動",
      removeFromProject: "{projectName} から外す",
      deleteChatTitle: "チャットを削除",
      deleteChatConfirmation:
        "このチャットを削除しますか？この操作は元に戻せません。",
      createProject: "{projectName} を作成",
      failedToDeleteChat:
        "チャットの削除に失敗しました。もう一度お試しください。",
      failedToCreateProject:
        "プロジェクトの作成に失敗しました。もう一度お試しください。",
    },
    time: {
      second: "秒",
      minute: "分",
      hour: "時間",
      day: "日",
      week: "週",
      month: "か月",
      year: "年",
      ago: "{count}{unit}前",
      today: "今日",
      yesterday: "昨日",
    },
  },
};

function normalizeLocaleInput(input?: string | null): Locale {
  if (!input) {
    return DEFAULT_LOCALE;
  }

  return input.toLowerCase().startsWith("ja") ? "ja" : "en";
}

function interpolate(
  template: string,
  values?: Record<string, string | number>
): string {
  if (!values) {
    return template;
  }

  return template.replace(/\{(\w+)\}/g, (_, key) => `${values[key] ?? ""}`);
}

function lookupTranslation(
  locale: Locale,
  key: string
): string | undefined {
  const segments = key.split(".");
  let current: TranslationValue | undefined = dictionaries[locale];

  for (const segment of segments) {
    if (!current || typeof current === "string") {
      return undefined;
    }
    current = current[segment];
  }

  return typeof current === "string" ? current : undefined;
}

export function getCurrentLocale(): Locale {
  if (typeof window !== "undefined") {
    const storedLocale = window.localStorage.getItem("onyx-locale");
    if (storedLocale) {
      return normalizeLocaleInput(storedLocale);
    }
  }

  if (typeof document !== "undefined" && document.documentElement.lang) {
    return normalizeLocaleInput(document.documentElement.lang);
  }

  return DEFAULT_LOCALE;
}

export function getLocaleTag(locale: Locale = getCurrentLocale()): string {
  return locale === "ja" ? "ja-JP" : "en-US";
}

export function setLocale(locale: Locale) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("onyx-locale", locale);
  }

  if (typeof document !== "undefined") {
    document.documentElement.lang = locale;
  }
}

export function t(
  key: string,
  values?: Record<string, string | number>,
  locale: Locale = getCurrentLocale()
): string {
  const translation =
    lookupTranslation(locale, key) ?? lookupTranslation("en", key) ?? key;
  return interpolate(translation, values);
}

import { User } from "@/lib/types";
import { getCurrentLocale, getLocaleTag } from "@/lib/i18n";

function formatRelativeTime(
  value: number,
  unit: Intl.RelativeTimeFormatUnit,
  numeric: Intl.RelativeTimeFormatNumeric = "always"
) {
  return new Intl.RelativeTimeFormat(getLocaleTag(getCurrentLocale()), {
    numeric,
  }).format(value, unit);
}

export const timeAgo = (
  dateString: string | undefined | null
): string | null => {
  if (!dateString) {
    return null;
  }

  const date = new Date(dateString);
  const now = new Date();
  const secondsDiff = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (secondsDiff < 60) {
    return formatRelativeTime(-secondsDiff, "second");
  }

  const minutesDiff = Math.floor(secondsDiff / 60);
  if (minutesDiff < 60) {
    return formatRelativeTime(-minutesDiff, "minute");
  }

  const hoursDiff = Math.floor(minutesDiff / 60);
  if (hoursDiff < 24) {
    return formatRelativeTime(-hoursDiff, "hour");
  }

  const daysDiff = Math.floor(hoursDiff / 24);
  if (daysDiff < 30) {
    return formatRelativeTime(-daysDiff, "day");
  }

  const weeksDiff = Math.floor(daysDiff / 7);
  if (weeksDiff < 4) {
    return formatRelativeTime(-weeksDiff, "week");
  }

  const monthsDiff = Math.floor(daysDiff / 30);
  if (monthsDiff < 12) {
    return formatRelativeTime(-monthsDiff, "month");
  }

  const yearsDiff = Math.floor(monthsDiff / 12);
  return formatRelativeTime(-yearsDiff, "year");
};

export function localizeAndPrettify(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

export function humanReadableFormat(dateString: string): string {
  const date = new Date(dateString);
  const formatter = new Intl.DateTimeFormat(getLocaleTag(getCurrentLocale()), {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  return formatter.format(date);
}

/**
 * Format a date as "Jan 15, 2025" (short month name).
 */
export function humanReadableFormatShort(date: string | Date | null): string {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  const formatter = new Intl.DateTimeFormat(getLocaleTag(getCurrentLocale()), {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  return formatter.format(d);
}

export function humanReadableFormatWithTime(datetimeString: string): string {
  const date = new Date(datetimeString);
  const formatter = new Intl.DateTimeFormat(getLocaleTag(getCurrentLocale()), {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "numeric",
  });
  return formatter.format(date);
}

export function getSecondsUntilExpiration(
  userInfo: User | null
): number | null {
  if (!userInfo) {
    return null;
  }

  const { oidc_expiry, current_token_created_at, current_token_expiry_length } =
    userInfo;

  const now = new Date();

  let secondsUntilTokenExpiration: number | null = null;
  let secondsUntilOIDCExpiration: number | null = null;

  if (current_token_created_at && current_token_expiry_length !== undefined) {
    const createdAt = new Date(current_token_created_at);
    const expiresAt = new Date(
      createdAt.getTime() + current_token_expiry_length * 1000
    );
    secondsUntilTokenExpiration = Math.floor(
      (expiresAt.getTime() - now.getTime()) / 1000
    );
  }

  if (oidc_expiry) {
    const expiresAtFromOIDC = new Date(oidc_expiry);
    secondsUntilOIDCExpiration = Math.floor(
      (expiresAtFromOIDC.getTime() - now.getTime()) / 1000
    );
  }

  if (
    secondsUntilTokenExpiration === null &&
    secondsUntilOIDCExpiration === null
  ) {
    return null;
  }

  return Math.max(
    0,
    Math.min(
      secondsUntilTokenExpiration ?? Infinity,
      secondsUntilOIDCExpiration ?? Infinity
    )
  );
}

export type TimeFilter = "day" | "week" | "month" | "year";

export function getTimeFilterDate(filter: TimeFilter): Date | null {
  const now = new Date();
  switch (filter) {
    case "day":
      return new Date(now.getTime() - 24 * 60 * 60 * 1000);
    case "week":
      return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    case "month":
      return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    case "year":
      return new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
    default:
      return null;
  }
}

export function formatDurationSeconds(seconds: number): string {
  const totalSeconds = Math.ceil(seconds);
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  }
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

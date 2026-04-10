import uz from "./uz.json";
import ru from "./ru.json";
import en from "./en.json";

export const locales = { uz, ru, en } as const;
export type Locale = keyof typeof locales;
export const defaultLocale: Locale = "ru";

export function t(locale: Locale, key: string, params?: Record<string, string | number>): string {
  const keys = key.split(".");
  let value: unknown = locales[locale];

  for (const k of keys) {
    if (value && typeof value === "object") {
      value = (value as Record<string, unknown>)[k];
    } else {
      return key;
    }
  }

  if (typeof value !== "string") return key;

  if (params) {
    return Object.entries(params).reduce(
      (str, [k, v]) => str.replace(`{${k}}`, String(v)),
      value
    );
  }

  return value;
}

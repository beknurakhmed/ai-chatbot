"use client";

import { useAppStore } from "@/lib/store";
import type { Locale } from "@/i18n";

const languages: { code: Locale; label: string; short: string }[] = [
  { code: "uz", label: "O'zbek", short: "UZ" },
  { code: "ru", label: "Русский", short: "RU" },
  { code: "en", label: "English", short: "EN" },
  { code: "kr", label: "한국어", short: "KR" },
];

export default function LanguageSwitcher() {
  const locale = useAppStore((s) => s.locale);
  const setLocale = useAppStore((s) => s.setLocale);

  return (
    <div className="flex gap-1.5">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLocale(lang.code)}
          className={`px-3 py-2 rounded-xl text-sm font-bold transition-all
            ${
              locale === lang.code
                ? "bg-blue-500 text-white shadow-md"
                : "bg-white/80 text-gray-600 hover:bg-white hover:shadow-sm"
            }`}
        >
          {lang.short}
        </button>
      ))}
    </div>
  );
}

"use client";

import { useAppStore } from "@/lib/store";
import type { Locale } from "@/i18n";

const languages: { code: Locale; label: string }[] = [
  { code: "uz", label: "O'zbek" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
  { code: "kr", label: "한국어" },
];

export default function LanguageSwitcher() {
  const locale = useAppStore((s) => s.locale);
  const setLocale = useAppStore((s) => s.setLocale);

  return (
    <div className="flex bg-gray-100 rounded-2xl p-1 gap-0.5">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLocale(lang.code)}
          className={`px-3 py-1.5 rounded-xl text-sm font-semibold transition-all
            ${
              locale === lang.code
                ? "bg-blue-500 text-white shadow-md"
                : "text-gray-500 hover:text-gray-800 hover:bg-white/60"
            }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}

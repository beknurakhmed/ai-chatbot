"use client";

import { useAppStore } from "@/lib/store";
import type { Locale } from "@/i18n";

const ALL_LANGUAGES: { code: Locale; label: string }[] = [
  { code: "uz", label: "O'zbek" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

const enabledCodes = (process.env.NEXT_PUBLIC_LANGUAGES || "uz,ru,en").split(",").map((s) => s.trim());
const languages = ALL_LANGUAGES.filter((l) => enabledCodes.includes(l.code));

export default function LanguageSwitcher() {
  const locale = useAppStore((s) => s.locale);
  const setLocale = useAppStore((s) => s.setLocale);

  return (
    <div className="flex bg-gray-100 rounded-2xl p-0.5 gap-0.5">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLocale(lang.code)}
          className={`px-2 py-1.5 md:px-3 md:py-1.5 rounded-xl text-xs md:text-sm font-semibold
            transition-colors duration-200 cursor-pointer focus:outline-none
            ${
              locale === lang.code
                ? "bg-purple-600 text-white shadow-sm"
                : "text-gray-500 hover:text-gray-800 hover:bg-white/60"
            }`}
        >
          <span className="hidden sm:inline">{lang.label}</span>
          <span className="sm:hidden">{lang.code.toUpperCase()}</span>
        </button>
      ))}
    </div>
  );
}

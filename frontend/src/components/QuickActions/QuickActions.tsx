"use client";

import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import { useChat } from "@/hooks/useChat";

const icons = {
  onboarding: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 11l3 3L22 4" /><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
    </svg>
  ),
  tools: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" />
    </svg>
  ),
  team: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4-4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  benefits: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  ),
  help: (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
};

const actions = [
  { key: "onboarding", icon: icons.onboarding, bg: "bg-purple-500/10 hover:bg-purple-500/20 text-purple-700 border-purple-200" },
  { key: "tools", icon: icons.tools, bg: "bg-blue-500/10 hover:bg-blue-500/20 text-blue-700 border-blue-200" },
  { key: "team", icon: icons.team, bg: "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 border-emerald-200" },
  { key: "benefits", icon: icons.benefits, bg: "bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 border-amber-200" },
  { key: "help", icon: icons.help, bg: "bg-teal-500/10 hover:bg-teal-500/20 text-teal-700 border-teal-200" },
];

export default function QuickActions() {
  const locale = useAppStore((s) => s.locale);
  const { send } = useChat();

  async function handleAction(key: string) {
    const label = t(locale, `quickActions.${key}`);
    await send(label);
  }

  return (
    <div className="flex flex-wrap justify-center gap-2 px-4 w-full max-w-xl mx-auto">
      {actions.map((action, i) => (
        <motion.button
          key={action.key}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.05, type: "spring", stiffness: 300 }}
          whileTap={{ scale: 0.93 }}
          onClick={() => handleAction(action.key)}
          className={`${action.bg} border rounded-full cursor-pointer
                      px-3.5 py-2 md:px-5 md:py-2.5
                      text-xs md:text-sm font-semibold
                      transition-colors duration-200 flex items-center gap-1.5 md:gap-2
                      focus:outline-none focus:ring-2 focus:ring-purple-400 focus:ring-offset-1
                      active:scale-95`}
        >
          {action.icon}
          {t(locale, `quickActions.${action.key}`)}
        </motion.button>
      ))}
    </div>
  );
}

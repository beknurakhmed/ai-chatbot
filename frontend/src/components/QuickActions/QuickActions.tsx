"use client";

import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import { useChat } from "@/hooks/useChat";
import { useTts } from "@/hooks/useTts";

const actions = [
  { key: "timetable", icon: "📅", bg: "bg-blue-500/10 hover:bg-blue-500/20 text-blue-700 border-blue-200" },
  { key: "map", icon: "🗺️", bg: "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-700 border-emerald-200" },
  { key: "news", icon: "📰", bg: "bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 border-amber-200" },
  { key: "staff", icon: "👨‍🏫", bg: "bg-purple-500/10 hover:bg-purple-500/20 text-purple-700 border-purple-200" },
  { key: "freeRooms", icon: "🚪", bg: "bg-teal-500/10 hover:bg-teal-500/20 text-teal-700 border-teal-200" },
];

export default function QuickActions() {
  const locale = useAppStore((s) => s.locale);
  const { send } = useChat();
  const { stop } = useTts();

  async function handleAction(key: string) {
    const label = t(locale, `quickActions.${key}`);
    stop();
    useAppStore.getState().setTtsEnabled(true);
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
          className={`${action.bg} border rounded-full
                      px-3.5 py-1.5 md:px-5 md:py-2.5
                      text-xs md:text-sm font-semibold
                      transition-all flex items-center gap-1.5 md:gap-2`}
        >
          <span className="text-sm md:text-base">{action.icon}</span>
          {t(locale, `quickActions.${action.key}`)}
        </motion.button>
      ))}
    </div>
  );
}

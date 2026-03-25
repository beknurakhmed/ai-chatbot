"use client";

import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import { useChat } from "@/hooks/useChat";

const actions = [
  { key: "timetable", icon: "📅", color: "from-blue-400 to-blue-500" },
  { key: "map", icon: "🗺️", color: "from-emerald-400 to-emerald-500" },
  { key: "faq", icon: "❓", color: "from-purple-400 to-purple-500" },
  { key: "contacts", icon: "📞", color: "from-orange-400 to-orange-500" },
  { key: "admission", icon: "🎓", color: "from-pink-400 to-pink-500" },
];

export default function QuickActions() {
  const locale = useAppStore((s) => s.locale);
  const { send } = useChat();

  async function handleAction(key: string) {
    const label = t(locale, `quickActions.${key}`);
    await send(label);
    // TTS handled automatically by useAutoTts
  }

  return (
    <div className="flex flex-wrap justify-center gap-3 px-4">
      {actions.map((action, i) => (
        <motion.button
          key={action.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => handleAction(action.key)}
          className={`bg-gradient-to-br ${action.color} text-white rounded-2xl
                      px-5 py-3 text-base md:text-lg font-medium shadow-md
                      hover:shadow-lg transition-shadow flex items-center gap-2`}
        >
          <span className="text-xl">{action.icon}</span>
          {t(locale, `quickActions.${action.key}`)}
        </motion.button>
      ))}
    </div>
  );
}

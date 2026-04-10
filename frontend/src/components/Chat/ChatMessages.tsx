"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";

const CATEGORY_LABELS: Record<string, Record<string, string>> = {
  day_1: { ru: "День 1", uz: "1-kun", en: "Day 1" },
  week_1: { ru: "Неделя 1", uz: "1-hafta", en: "Week 1" },
  week_2: { ru: "Неделя 2", uz: "2-hafta", en: "Week 2" },
  month_1: { ru: "Месяц 1", uz: "1-oy", en: "Month 1" },
};

export default function ChatMessages() {
  const messages = useAppStore((s) => s.messages);
  const isLoading = useAppStore((s) => s.isLoading);
  const locale = useAppStore((s) => s.locale);
  const ttsPreparingId = useAppStore((s) => s.ttsPreparingId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) return null;

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-3 space-y-3 max-h-[50vh] scrollbar-thin"
    >
      {messages.map((msg) => (
        <motion.div
          key={msg.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[85%] md:max-w-[75%] px-4 py-3 rounded-2xl text-sm md:text-base leading-relaxed ${
              msg.role === "user"
                ? "bg-purple-600 text-white rounded-br-sm"
                : "bg-white text-gray-800 border border-purple-100/80 rounded-bl-sm shadow-sm"
            }`}
          >
            {ttsPreparingId === msg.id ? (
              <span className="flex items-center gap-1 text-gray-400">
                <span className="animate-bounce">{"\u25CF"}</span>
                <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>{"\u25CF"}</span>
                <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>{"\u25CF"}</span>
              </span>
            ) : (
              <span className="whitespace-pre-line">{msg.content}</span>
            )}

            {/* Onboarding checklist */}
            {msg.onboarding && msg.onboarding.length > 0 && (
              <div className="mt-3 space-y-3">
                {Object.entries(
                  msg.onboarding.reduce((acc, task) => {
                    if (!acc[task.category]) acc[task.category] = [];
                    acc[task.category].push(task);
                    return acc;
                  }, {} as Record<string, typeof msg.onboarding>)
                ).map(([category, tasks]) => (
                  <div key={category}>
                    <div className="text-xs font-bold text-purple-600 uppercase mb-1">
                      {CATEGORY_LABELS[category]?.[locale] || category}
                    </div>
                    <div className="space-y-1">
                      {tasks.map((task) => (
                        <div
                          key={task.id}
                          className="flex items-start gap-2 bg-purple-50 rounded-lg px-3 py-2 text-sm"
                        >
                          <span className="text-purple-400 mt-0.5">{"\u25CB"}</span>
                          <div>
                            <div className="font-medium text-gray-800">{task.title}</div>
                            {task.description && (
                              <div className="text-gray-500 text-xs mt-0.5">{task.description}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      ))}

      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-start"
        >
          <div className="bg-white text-gray-500 px-4 py-3 rounded-2xl rounded-bl-md border border-purple-100 shadow-sm">
            <span className="flex items-center gap-1">
              <span className="animate-bounce">{"\u25CF"}</span>
              <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>{"\u25CF"}</span>
              <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>{"\u25CF"}</span>
              <span className="ml-2">{t(locale, "chat.thinking")}</span>
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
}

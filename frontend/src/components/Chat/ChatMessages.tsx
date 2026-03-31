"use client";

import { useEffect, useRef, useMemo } from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import TimetableView from "./TimetableView";
import StaffCard from "./StaffCard";
import NewsCard from "./NewsCard";
import CampusMap from "./CampusMap";

interface ChatMessagesProps {
  hideLastAssistant?: boolean;
}

export default function ChatMessages({ hideLastAssistant }: ChatMessagesProps) {
  const messages = useAppStore((s) => s.messages);
  const isLoading = useAppStore((s) => s.isLoading);
  const locale = useAppStore((s) => s.locale);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Find the last assistant message id to optionally hide it
  const lastAssistantId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant") return messages[i].id;
    }
    return null;
  }, [messages]);

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
      {messages.map((msg) => {
        // Hide last assistant message when it's being shown in the speech bubble
        if (hideLastAssistant && msg.id === lastAssistantId && msg.role === "assistant") {
          return null;
        }

        return (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[90%] px-4 py-3 rounded-2xl text-sm md:text-base ${
                msg.role === "user"
                  ? "bg-blue-500 text-white rounded-br-md"
                  : "bg-white text-gray-800 border border-blue-100 rounded-bl-md shadow-sm"
              }`}
            >
              {msg.content}
              {/* Campus map with legend */}
              {msg.map && <CampusMap />}
              {/* Staff cards */}
              {msg.staff && msg.staff.length > 0 && (
                <StaffCard staff={msg.staff} />
              )}
              {/* News cards with QR codes */}
              {msg.news && msg.news.length > 0 && (
                <NewsCard news={msg.news} />
              )}
              {/* Timetable table */}
              {msg.timetable && (
                <div className="mt-2">
                  <TimetableView
                    group={msg.timetable.group}
                    lessons={msg.timetable.lessons}
                  />
                </div>
              )}
            </div>
          </motion.div>
        );
      })}

      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-start"
        >
          <div className="bg-white text-gray-500 px-4 py-3 rounded-2xl rounded-bl-md border border-blue-100 shadow-sm">
            <span className="flex items-center gap-1">
              <span className="animate-bounce">●</span>
              <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>●</span>
              <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>●</span>
              <span className="ml-2">{t(locale, "chat.thinking")}</span>
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
}

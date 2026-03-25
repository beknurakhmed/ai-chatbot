"use client";

import { useState, type FormEvent } from "react";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import { useChat } from "@/hooks/useChat";
import { useTts } from "@/hooks/useTts";

export default function ChatInput() {
  const [input, setInput] = useState("");
  const locale = useAppStore((s) => s.locale);
  const { send, isLoading } = useChat();
  const { isSpeaking, stop } = useTts();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    if (isSpeaking) stop();
    await send(text);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-4 py-3 items-center">
      {/* Listening indicator */}
      <div className="shrink-0 w-12 h-12 rounded-xl flex items-center justify-center bg-green-100 text-green-500 animate-pulse">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" x2="12" y1="19" y2="22" />
        </svg>
      </div>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={t(locale, "inputPlaceholder")}
        className="flex-1 bg-white border-2 border-blue-200 rounded-xl px-5 py-3 text-lg
                   focus:outline-none focus:border-blue-400 transition-colors placeholder:text-gray-400"
        disabled={isLoading}
      />

      {isSpeaking && (
        <button
          type="button"
          onClick={stop}
          className="shrink-0 w-12 h-12 rounded-xl bg-blue-100 text-blue-500
                     flex items-center justify-center hover:bg-blue-200 transition-colors"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        </button>
      )}

      <button
        type="submit"
        disabled={isLoading || !input.trim()}
        className="shrink-0 w-12 h-12 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300
                   text-white rounded-xl flex items-center justify-center transition-colors active:scale-95 transform"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m22 2-7 20-4-9-9-4z" />
          <path d="M22 2 11 13" />
        </svg>
      </button>
    </form>
  );
}

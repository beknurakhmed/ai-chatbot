"use client";

import { useState, type FormEvent } from "react";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";
import { useChat } from "@/hooks/useChat";

function TtsToggle() {
  const ttsEnabled = useAppStore((s) => s.ttsEnabled);
  const setTtsEnabled = useAppStore((s) => s.setTtsEnabled);
  return (
    <button
      type="button"
      onClick={() => setTtsEnabled(!ttsEnabled)}
      className={`shrink-0 w-10 h-10 md:w-12 md:h-12 rounded-xl flex items-center justify-center transition-colors duration-200 cursor-pointer
        focus:outline-none focus:ring-2 focus:ring-purple-300 ${
        ttsEnabled
          ? "bg-purple-100 text-purple-600"
          : "bg-gray-100 text-gray-400 hover:bg-gray-200"
      }`}
      title={ttsEnabled ? "TTS ON" : "TTS OFF"}
    >
      <svg className="w-4 h-4 md:w-5 md:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {ttsEnabled ? (
          <>
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
            <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
          </>
        ) : (
          <>
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <line x1="23" y1="9" x2="17" y2="15" />
            <line x1="17" y1="9" x2="23" y2="15" />
          </>
        )}
      </svg>
    </button>
  );
}

export default function ChatInput() {
  const [input, setInput] = useState("");
  const locale = useAppStore((s) => s.locale);
  const { send, isLoading } = useChat();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    await send(text);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 px-3 md:px-4 py-2.5 md:py-3 items-center">
      <TtsToggle />
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={t(locale, "inputPlaceholder")}
        className="flex-1 bg-white border-2 border-purple-200 rounded-xl px-4 md:px-5 py-2.5 md:py-3 text-base
                   focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100
                   transition-colors duration-200 placeholder:text-gray-400"
        disabled={isLoading}
      />

      <button
        type="submit"
        disabled={isLoading || !input.trim()}
        className="shrink-0 w-10 h-10 md:w-12 md:h-12 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300
                   text-white rounded-xl flex items-center justify-center transition-colors duration-200
                   cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-400 active:scale-95"
      >
        <svg className="w-4 h-4 md:w-5 md:h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m22 2-7 20-4-9-9-4z" />
          <path d="M22 2 11 13" />
        </svg>
      </button>
    </form>
  );
}

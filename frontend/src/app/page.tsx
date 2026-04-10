"use client";

import { motion } from "framer-motion";
import Uzumchi from "@/components/Chito/Chito";
import ChatMessages from "@/components/Chat/ChatMessages";
import ChatInput from "@/components/Chat/ChatInput";
import QuickActions from "@/components/QuickActions/QuickActions";
import LanguageSwitcher from "@/components/LanguageSwitcher/LanguageSwitcher";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";

export default function HomePage() {
  const locale = useAppStore((s) => s.locale);
  const messages = useAppStore((s) => s.messages);
  const setMood = useAppStore((s) => s.setMood);
  const clearMessages = useAppStore((s) => s.clearMessages);
  const showWelcome = messages.length === 0;

  function handleReset() {
    clearMessages();
    setMood("greeting");
  }

  return (
    <div className="flex flex-col h-full relative">
      {/* Header */}
      <header className="flex items-center justify-between px-4 md:px-6 py-2.5 md:py-3 bg-white/80 backdrop-blur-md border-b border-purple-100/60 sticky top-0 z-30">
        <div className="flex items-center gap-2.5 md:gap-3 min-w-0">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/uzum-logo.png" alt="Uzum" className="h-8 md:h-10 w-auto flex-shrink-0 rounded-xl" />
          <h1 className="text-sm md:text-lg font-semibold text-gray-800 truncate font-[var(--font-poppins)]">
            <span className="text-purple-700">Uzum</span> Onboarding
          </h1>
        </div>
        <div className="flex items-center gap-1.5 md:gap-2 flex-shrink-0">
          {!showWelcome && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium cursor-pointer
                         bg-red-50 text-red-500 hover:bg-red-100 transition-colors duration-200
                         focus:outline-none focus:ring-2 focus:ring-red-300"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 12a9 9 0 1 1 9 9 9.75 9.75 0 0 1-6.74-2.74L3 21" />
                <path d="M3 3v6h6" />
              </svg>
              <span className="hidden sm:inline">New chat</span>
            </button>
          )}
          <LanguageSwitcher />
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col items-center py-1 md:py-3 overflow-hidden">
        {/* Mascot */}
        <motion.div
          className="flex flex-col items-center gap-1 md:gap-3 flex-shrink-0"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Uzumchi />
        </motion.div>

        {/* Welcome subtitle */}
        {showWelcome && (
          <>
            <motion.h2
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-lg md:text-2xl font-bold text-gray-800 text-center px-4"
            >
              {t(locale, "welcome")}
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="text-gray-500 text-xs md:text-base text-center px-4 mt-1 md:mt-2"
            >
              {t(locale, "welcomeSub")}
            </motion.p>
          </>
        )}

        {/* Chat messages */}
        <div className="w-full max-w-2xl flex-1 flex flex-col min-h-0 mt-2">
          <ChatMessages />
        </div>

        {/* Quick actions */}
        {showWelcome && (
          <div className="flex-shrink-0 w-full max-w-2xl mt-3">
            <QuickActions />
          </div>
        )}
      </main>

      {/* Chat input */}
      <footer className="bg-white/70 backdrop-blur-sm border-t border-purple-100 w-full">
        <div className="max-w-2xl mx-auto">
          <ChatInput />
        </div>
      </footer>
    </div>
  );
}

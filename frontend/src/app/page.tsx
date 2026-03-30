"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Chito from "@/components/Chito/Chito";
import SpeechBubble from "@/components/Chito/SpeechBubble";
import ChatMessages from "@/components/Chat/ChatMessages";
import ChatInput from "@/components/Chat/ChatInput";
import QuickActions from "@/components/QuickActions/QuickActions";
import LanguageSwitcher from "@/components/LanguageSwitcher/LanguageSwitcher";
import { useAppStore } from "@/lib/store";
import { useKioskMode } from "@/hooks/useKioskMode";
import { useAutoTts } from "@/hooks/useAutoTts";
import { useStt } from "@/hooks/useStt";
import { useChat } from "@/hooks/useChat";
import { useTts } from "@/hooks/useTts";
import { useTypewriter } from "@/hooks/useTypewriter";
import { t } from "@/i18n";

export default function KioskPage() {
  const locale = useAppStore((s) => s.locale);
  const messages = useAppStore((s) => s.messages);
  const setMood = useAppStore((s) => s.setMood);
  const clearMessages = useAppStore((s) => s.clearMessages);
  const isLoading = useAppStore((s) => s.isLoading);
  const userName = useAppStore((s) => s.userName);
  const addMessage = useAppStore((s) => s.addMessage);
  const { state, videoRef, markActive, registerFace } = useKioskMode();
  useAutoTts();

  const { send } = useChat();
  const { isSpeaking, stop: stopTts } = useTts();
  const { startListening, stopListening, isListening, transcript } = useStt();
  const sttActiveRef = useRef(false);

  const YES_WORDS = ["да", "yes", "ха", "верно", "правильно", "ha", "to'g'ri", "네", "맞아"];
  const NO_WORDS = ["нет", "no", "йўқ", "yo'q", "неправильно", "아니", "아니요"];

  // Extract name from spelled letters: "Б Е К Н У Р" → "Бекнур", "B E K N U R" → "Beknur"
  function parseSpelledName(text: string): string {
    // Remove filler words, punctuation, keep only single letters/chars
    const cleaned = text.replace(/[.,!?:;'"()-]/g, "").trim();
    const parts = cleaned.split(/\s+/);

    // If all parts are single characters → spelling mode
    const allSingleChar = parts.length >= 2 && parts.every((p) => p.length === 1);
    if (allSingleChar) {
      // Join letters: first uppercase, rest lowercase
      const joined = parts.join("");
      return joined.charAt(0).toUpperCase() + joined.slice(1).toLowerCase();
    }

    // Otherwise treat first word as name
    const name = parts[0].replace(/[.,!?]/g, "");
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  }

  // Auto-start STT when kiosk is active, stop when sleeping/loading
  useEffect(() => {
    const shouldListen = (state === "active" || state === "idle") && !isSpeaking && !isLoading;

    if (shouldListen && !sttActiveRef.current) {
      sttActiveRef.current = true;
      startListening(async (text) => {
        markActive();
        if (isSpeaking) stopTts();

        const store = useAppStore.getState();
        const textLower = text.trim().toLowerCase();

        // Activate TTS when user says "hi chito" via voice
        const GREETING_TRIGGERS = [
          "hi chito", "hey chito", "hello chito",
          "привет чито", "салом чито", "хей чито",
          "salom chito", "안녕 치토",
        ];
        if (GREETING_TRIGGERS.some((t) => textLower.includes(t))) {
          useAppStore.getState().setTtsEnabled(true);
        }

        // STEP 2: Waiting for confirmation ("да" / "нет" / re-spell)
        if (store.waitingForConfirmation && store.pendingName) {
          addMessage({ role: "user", content: text });

          if (YES_WORDS.some((w) => textLower.includes(w))) {
            // Confirmed — register face
            const ok = await registerFace(store.pendingName);
            useAppStore.getState().setWaitingForConfirmation(false);
            useAppStore.getState().setPendingName(null);
            useAppStore.getState().setWaitingForName(false);

            if (ok) {
              setMood("happy");
              const msgs: Record<string, string> = {
                uz: `Ajoyib, ${store.pendingName}! Men sizni eslab qoldim! Sizga qanday yordam bera olaman?`,
                ru: `Отлично, ${store.pendingName}! Я тебя запомнил! Чем могу помочь?`,
                en: `Great, ${store.pendingName}! I'll remember you! How can I help?`,
                kr: `좋아요, ${store.pendingName}님! 기억할게요! 무엇을 도와드릴까요?`,
              };
              addMessage({ role: "assistant", content: msgs[locale] || msgs.en, mood: "happy" });
            } else {
              setMood("sad");
              const msgs: Record<string, string> = {
                uz: `${store.pendingName}, yuzingizni ko'ra olmadim. Kameraga qarang va ismingizni qayta ayting.`,
                ru: `${store.pendingName}, не смог увидеть лицо. Посмотри в камеру и произнеси имя по буквам ещё раз.`,
                en: `${store.pendingName}, I couldn't see your face. Look at the camera and spell your name again.`,
                kr: `얼굴을 볼 수 없었어요. 카메라를 보고 다시 철자해주세요.`,
              };
              useAppStore.getState().setWaitingForName(true);
              addMessage({ role: "assistant", content: msgs[locale] || msgs.en, mood: "sad" });
            }
          } else if (NO_WORDS.some((w) => textLower.includes(w))) {
            // Denied — ask to spell again
            useAppStore.getState().setWaitingForConfirmation(false);
            useAppStore.getState().setPendingName(null);
            useAppStore.getState().setWaitingForName(true);
            setMood("curious");
            const msgs: Record<string, string> = {
              uz: "Kechirasiz! Ismingizni qayta harf-harf ayting.",
              ru: "Извини! Произнеси имя по буквам ещё раз.",
              en: "Sorry! Spell your name again letter by letter.",
              kr: "죄송합니다! 이름을 다시 한 글자씩 말해주세요.",
            };
            addMessage({ role: "assistant", content: msgs[locale] || msgs.en, mood: "curious" });
          } else {
            // Treat as a new spelling attempt
            const newName = parseSpelledName(text);
            if (newName) {
              useAppStore.getState().setPendingName(newName);
              const msgs: Record<string, string> = {
                uz: `${newName} — to'g'rimi?`,
                ru: `${newName} — правильно?`,
                en: `${newName} — is that correct?`,
                kr: `${newName} — 맞나요?`,
              };
              addMessage({ role: "assistant", content: msgs[locale] || msgs.en, mood: "curious" });
            }
          }
          return;
        }

        // STEP 1: Waiting for name — user spells their name
        if (store.waitingForName) {
          const name = parseSpelledName(text);
          if (name) {
            addMessage({ role: "user", content: text });
            useAppStore.getState().setPendingName(name);
            useAppStore.getState().setWaitingForName(false);
            useAppStore.getState().setWaitingForConfirmation(true);

            const msgs: Record<string, string> = {
              uz: `${name} — to'g'rimi?`,
              ru: `${name} — правильно?`,
              en: `${name} — is that correct?`,
              kr: `${name} — 맞나요?`,
            };
            addMessage({ role: "assistant", content: msgs[locale] || msgs.en, mood: "curious" });
          }
          return;
        }

        // Normal chat
        await send(text);
      });
    } else if (!shouldListen && sttActiveRef.current) {
      sttActiveRef.current = false;
      stopListening();
    }
  }, [state, isSpeaking, isLoading, startListening, stopListening, send, markActive, stopTts, addMessage, locale, registerFace, setMood]);

  // useAutoTts handles all speech automatically

  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
  const fullBubbleText = lastAssistantMsg?.content || t(locale, "welcome");
  const showWelcome = messages.length === 0;
  const { displayed: typedText, isTyping: isBubbleTyping } = useTypewriter(fullBubbleText, isSpeaking);
  const bubbleText = lastAssistantMsg ? (typedText || "") : fullBubbleText;

  function handleReset() {
    clearMessages();
    setMood("greeting");
    useAppStore.getState().setTtsEnabled(false);
  }

  const isSleeping = state === "sleeping";

  return (
    <div className="flex flex-col h-full relative" onClick={markActive}>
      {/* Hidden camera video for face detection */}
      <video
        ref={videoRef}
        className="hidden"
        playsInline
        muted
        autoPlay
      />

      {/* Sleep overlay */}
      <AnimatePresence>
        {isSleeping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1 }}
            className="absolute inset-0 z-50 bg-gradient-to-b from-[#0a1628] to-[#1a2744] flex flex-col items-center justify-center cursor-pointer"
            onClick={markActive}
          >
            {/* Sleeping Chito — centered */}
            <motion.div
              animate={{ y: [0, -10, 0], scale: [1, 1.02, 1] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="w-56 h-56 md:w-72 md:h-72 relative opacity-60"
            >
              <Chito />
            </motion.div>

            {/* Zzz */}
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3], y: [0, -20, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-blue-300/50 text-4xl font-bold mt-6"
            >
              z z z
            </motion.div>

            {/* Tap hint */}
            <motion.p
              animate={{ opacity: [0.3, 0.7, 0.3] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-blue-300/40 text-sm mt-12"
            >
              Tap or step closer to wake Chito
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="flex items-center justify-between px-4 md:px-6 py-3 bg-white/60 backdrop-blur-sm border-b border-blue-100">
        <div className="flex items-center gap-3">
          <img src="/ajou-logo.png" alt="Ajou University in Tashkent" className="h-10 w-auto" />
          <h1 className="text-base md:text-lg font-bold text-gray-800">
            Ajou University in Tashkent
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {/* Status indicator */}
          <div className={`w-2 h-2 rounded-full ${state === "active" ? "bg-green-400" : state === "idle" ? "bg-yellow-400" : "bg-gray-300"}`} />

          {/* Show recognized user name */}
          {userName && (
            <span className="text-sm text-green-600 font-medium px-2">
              {userName}
            </span>
          )}

          {!showWelcome && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium
                         bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
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
      <main className="flex-1 flex flex-col items-center py-3 overflow-hidden">
        {/* Chito + bubble */}
        <motion.div
          className="flex flex-col items-center gap-3 flex-shrink-0"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Chito />
          {/* <SpeechBubble text={bubbleText} isVisible={!!bubbleText} isTyping={isBubbleTyping} /> */}
        </motion.div>

        {/* Real-time transcript indicator */}
        {transcript && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-green-50 border border-green-200 rounded-xl px-4 py-2 text-green-700 text-sm max-w-md text-center"
          >
            <span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse mr-2" />
            {transcript}
          </motion.div>
        )}

        {/* Welcome subtitle */}
        {showWelcome && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-gray-500 text-sm md:text-base text-center px-4 mt-2"
          >
            {t(locale, "welcomeSub")}
          </motion.p>
        )}

        {/* Chat messages */}
        <div className="w-full max-w-2xl flex-1 flex flex-col min-h-0 mt-2">
          <ChatMessages hideLastAssistant={false} />
        </div>

        {/* Quick actions */}
        {showWelcome && (
          <div className="flex-shrink-0 w-full max-w-2xl mt-2">
            <QuickActions />
          </div>
        )}
      </main>

      {/* Chat input */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-blue-100 w-full">
        <div className="max-w-2xl mx-auto">
          <ChatInput />
        </div>
      </footer>
    </div>
  );
}

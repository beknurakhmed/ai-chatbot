"use client";

import { useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { useTts } from "./useTts";

/**
 * Auto-speaks assistant messages only when TTS is enabled.
 * TTS is activated when user says "hi chito" via voice (STT).
 */
export function useAutoTts() {
  const messages = useAppStore((s) => s.messages);
  const ttsEnabled = useAppStore((s) => s.ttsEnabled);
  const { speak, stop } = useTts();
  const lastSpokenIdRef = useRef<string>("");

  useEffect(() => {
    if (!ttsEnabled || messages.length === 0) return;

    const lastMsg = messages[messages.length - 1];

    if (
      lastMsg.role === "assistant" &&
      lastMsg.id !== lastSpokenIdRef.current &&
      lastMsg.content
    ) {
      lastSpokenIdRef.current = lastMsg.id;
      stop();
      speak(lastMsg.content);
    }
  }, [messages, ttsEnabled, speak, stop]);
}

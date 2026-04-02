"use client";

import { useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { useTts } from "./useTts";

/**
 * Auto-speaks assistant messages only when TTS is enabled.
 * Sets ttsPreparingId while audio is loading so ChatMessages can hide text.
 * Clears it when the first audio chunk starts playing.
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

      // Mark this message as "preparing TTS" — text will be hidden
      useAppStore.getState().setTtsPreparingId(lastMsg.id);

      speak(lastMsg.content, () => {
        // First audio chunk ready — reveal the text
        useAppStore.getState().setTtsPreparingId(null);
      });
    }
  }, [messages, ttsEnabled, speak, stop]);
}

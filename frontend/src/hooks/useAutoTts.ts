"use client";

import { useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { useTts } from "./useTts";

/**
 * Auto-speaks every new assistant message.
 * Mount once in the root page component.
 */
export function useAutoTts() {
  const messages = useAppStore((s) => s.messages);
  const { speak, stop } = useTts();
  const lastSpokenIdRef = useRef<string>("");

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMsg = messages[messages.length - 1];

    // Only speak assistant messages, and only once
    if (
      lastMsg.role === "assistant" &&
      lastMsg.id !== lastSpokenIdRef.current &&
      lastMsg.content
    ) {
      lastSpokenIdRef.current = lastMsg.id;

      // Don't speak timetable data (too long)
      if (lastMsg.timetable) {
        // Just speak the intro text, not the table
        speak(lastMsg.content);
      } else {
        stop();
        speak(lastMsg.content);
      }
    }
  }, [messages, speak, stop]);
}

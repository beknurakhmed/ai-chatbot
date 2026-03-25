import { useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";

const IDLE_TIMEOUT = 2 * 60 * 1000; // 2 minutes

export function useIdleTimer() {
  const clearMessages = useAppStore((s) => s.clearMessages);
  const setMood = useAppStore((s) => s.setMood);
  const messages = useAppStore((s) => s.messages);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function resetTimer() {
      if (timerRef.current) clearTimeout(timerRef.current);

      // Only set idle timer if there are messages (active session)
      if (messages.length > 0) {
        timerRef.current = setTimeout(() => {
          clearMessages();
          setMood("greeting");
        }, IDLE_TIMEOUT);
      }
    }

    const events = ["mousedown", "touchstart", "keydown", "mousemove"];
    events.forEach((e) => window.addEventListener(e, resetTimer));
    resetTimer();

    return () => {
      events.forEach((e) => window.removeEventListener(e, resetTimer));
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [messages.length, clearMessages, setMood]);
}

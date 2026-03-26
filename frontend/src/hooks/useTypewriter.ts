import { useState, useEffect, useRef, useCallback } from "react";

const WORDS_PER_SECOND = 3.5;

/**
 * Reveals text word-by-word synced with TTS playback.
 * - When new text arrives: resets to empty, waits for isPlaying
 * - When isPlaying becomes true: starts typing word by word
 * - When isPlaying becomes false after typing started: shows full text
 */
export function useTypewriter(fullText: string, isPlaying: boolean) {
  const [displayed, setDisplayed] = useState(fullText);
  const [isTyping, setIsTyping] = useState(false);
  const wordsRef = useRef<string[]>([]);
  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevTextRef = useRef(fullText);
  const waitingForPlayRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // New text arrived — reset and wait for TTS
  useEffect(() => {
    if (fullText !== prevTextRef.current) {
      prevTextRef.current = fullText;
      clearTimer();
      wordsRef.current = fullText.split(/(\s+)/);
      indexRef.current = 0;
      waitingForPlayRef.current = true;
      setDisplayed("");
      setIsTyping(false);
    }
  }, [fullText, clearTimer]);

  // React to isPlaying changes
  useEffect(() => {
    if (isPlaying && waitingForPlayRef.current) {
      // TTS started — begin typing
      waitingForPlayRef.current = false;
      setIsTyping(true);
      const intervalMs = 1000 / WORDS_PER_SECOND / 2;

      timerRef.current = setInterval(() => {
        indexRef.current++;
        const slice = wordsRef.current.slice(0, indexRef.current).join("");
        setDisplayed(slice);

        if (indexRef.current >= wordsRef.current.length) {
          clearTimer();
          setIsTyping(false);
        }
      }, intervalMs);
    }

    if (!isPlaying && !waitingForPlayRef.current && prevTextRef.current) {
      // TTS ended — show full text
      clearTimer();
      setDisplayed(prevTextRef.current);
      setIsTyping(false);
      indexRef.current = wordsRef.current.length;
    }

    return () => clearTimer();
  }, [isPlaying, clearTimer]);

  return { displayed, isTyping };
}

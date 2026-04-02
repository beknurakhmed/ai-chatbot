import { useCallback } from "react";
import { useAppStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Shared state — singleton across all useTts instances
let currentAudio: HTMLAudioElement | null = null;
let currentGeneration = 0; // Incremented on each speak() to cancel previous

// Unlock audio on first user interaction (browser autoplay policy)
let audioUnlocked = false;
function unlockAudio() {
  if (audioUnlocked) return;
  const a = document.createElement("audio");
  a.src = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";
  a.play().then(() => { audioUnlocked = true; }).catch(() => {});
  a.remove();
}

if (typeof window !== "undefined") {
  ["click", "touchstart", "keydown"].forEach((evt) =>
    window.addEventListener(evt, unlockAudio, { once: true })
  );
}

/**
 * Split text into sentences for chunked TTS.
 * Handles: periods, exclamation, question marks, ellipsis.
 */
function splitSentences(text: string): string[] {
  // Split on sentence-ending punctuation, keeping the punctuation
  const parts = text.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g);
  if (!parts || parts.length === 0) return [text];
  return parts.map((s) => s.trim()).filter((s) => s.length > 0);
}

/** Play a single audio blob. Returns a promise that resolves when playback ends. */
function playBlob(blob: Blob): Promise<void> {
  return new Promise((resolve) => {
    const blobUrl = URL.createObjectURL(blob);
    const audio = document.createElement("audio");
    audio.src = blobUrl;
    document.body.appendChild(audio);
    currentAudio = audio;

    audio.onplay = () => useAppStore.getState().setIsSpeaking(true);

    const cleanup = () => {
      audio.remove();
      URL.revokeObjectURL(blobUrl);
      if (currentAudio === audio) currentAudio = null;
      resolve();
    };

    audio.onended = cleanup;
    audio.onerror = cleanup;

    audio.play().catch(() => {
      useAppStore.getState().setIsSpeaking(false);
      cleanup();
    });
  });
}

export function useTts() {
  const isSpeaking = useAppStore((s) => s.isSpeaking);

  /**
   * Speak text with sentence-level chunking.
   * - Splits text into sentences
   * - Fetches all sentence audio in parallel
   * - Plays them sequentially (first chunk plays ASAP)
   * - Calls onFirstChunkReady() when first audio is about to play
   */
  const speak = useCallback((text: string, onFirstChunkReady?: () => void) => {
    const locale = useAppStore.getState().locale;

    // Cancel previous playback
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.remove();
      currentAudio = null;
      useAppStore.getState().setIsSpeaking(false);
    }

    const gen = ++currentGeneration;
    const sentences = splitSentences(text);

    // Fetch all sentence audio in parallel
    const audioPromises = sentences.map((sentence) =>
      fetch(`${API_BASE}/api/tts?text=${encodeURIComponent(sentence)}&locale=${locale}`)
        .then((res) => {
          if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);
          return res.blob();
        })
        .catch(() => null)
    );

    // Play sequentially — first chunk plays as soon as it arrives
    (async () => {
      for (let i = 0; i < audioPromises.length; i++) {
        if (gen !== currentGeneration) return; // Cancelled

        const blob = await audioPromises[i];
        if (!blob || gen !== currentGeneration) return;

        // Signal when first chunk is ready to play
        if (i === 0 && onFirstChunkReady) onFirstChunkReady();

        await playBlob(blob);
      }
      // All chunks done
      if (gen === currentGeneration) {
        useAppStore.getState().setIsSpeaking(false);
      }
    })();
  }, []);

  const stop = useCallback(() => {
    currentGeneration++; // Cancel any in-flight playback
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.remove();
      currentAudio = null;
      useAppStore.getState().setIsSpeaking(false);
    }
  }, []);

  return { speak, stop, isSpeaking };
}

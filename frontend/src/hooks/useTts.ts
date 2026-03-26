import { useCallback, useEffect } from "react";
import { useAppStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Shared audio element — singleton across all useTts instances
let currentAudio: HTMLAudioElement | null = null;

// Unlock audio on first user interaction
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

export function useTts() {
  const isSpeaking = useAppStore((s) => s.isSpeaking);

  const speak = useCallback((text: string) => {
    const locale = useAppStore.getState().locale;

    // Stop previous
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.remove();
      currentAudio = null;
      useAppStore.getState().setIsSpeaking(false);
    }

    const url = `${API_BASE}/api/tts?text=${encodeURIComponent(text)}&locale=${locale}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    fetch(url, { signal: controller.signal })
      .then((res) => {
        clearTimeout(timeoutId);
        if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);
        return res.blob();
      })
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const audio = document.createElement("audio");
        audio.src = blobUrl;
        document.body.appendChild(audio);
        currentAudio = audio;

        audio.onplay = () => useAppStore.getState().setIsSpeaking(true);
        audio.onended = () => {
          useAppStore.getState().setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
          if (currentAudio === audio) currentAudio = null;
        };
        audio.onerror = () => {
          useAppStore.getState().setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
          if (currentAudio === audio) currentAudio = null;
        };

        audio.play().catch((err) => {
          console.error("TTS play failed:", err);
          useAppStore.getState().setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
          if (currentAudio === audio) currentAudio = null;
        });
      })
      .catch((err) => {
        console.error("TTS fetch failed:", err);
      });
  }, []);

  const stop = useCallback(() => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.remove();
      currentAudio = null;
      useAppStore.getState().setIsSpeaking(false);
    }
  }, []);

  return { speak, stop, isSpeaking };
}

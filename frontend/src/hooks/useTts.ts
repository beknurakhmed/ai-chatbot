import { useRef, useState, useCallback, useEffect } from "react";
import { useAppStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback((text: string) => {
    const locale = useAppStore.getState().locale;

    // Stop previous
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.remove();
      audioRef.current = null;
    }

    const url = `${API_BASE}/api/tts?text=${encodeURIComponent(text)}&locale=${locale}`;

    // Use fetch to download audio first, then play from blob
    // This avoids CORS issues with MediaElementSource
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

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
        audioRef.current = audio;

        audio.onplay = () => setIsSpeaking(true);
        audio.onended = () => {
          setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
          audioRef.current = null;
        };
        audio.onerror = () => {
          setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
          audioRef.current = null;
        };

        audio.play().catch((err) => {
          console.error("TTS play failed:", err);
          setIsSpeaking(false);
          audio.remove();
          URL.revokeObjectURL(blobUrl);
        });
      })
      .catch((err) => {
        console.error("TTS fetch failed:", err);
      });
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.remove();
      audioRef.current = null;
      setIsSpeaking(false);
    }
  }, []);

  return { speak, stop, isSpeaking };
}

import { useState, useCallback, useRef } from "react";
import { useAppStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useStt() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onResultRef = useRef<((text: string) => void) | null>(null);
  const stoppedRef = useRef(false);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const locale = useAppStore((s) => s.locale);

  const sendAudio = useCallback(async (blob: Blob) => {
    try {
      const formData = new FormData();
      formData.append("audio", blob, "audio.webm");
      formData.append("locale", locale);

      const res = await fetch(`${API_BASE}/api/stt`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) return;
      const data = await res.json();
      if (data.text && data.text.trim()) {
        setTranscript(data.text.trim());
        onResultRef.current?.(data.text.trim());
        setTranscript("");
      }
    } catch (err) {
      console.error("STT error:", err);
    }
  }, [locale]);

  const startListening = useCallback(
    (onResult: (text: string) => void) => {
      onResultRef.current = onResult;
      stoppedRef.current = false;

      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          streamRef.current = stream;
          setIsListening(true);

          const startRecording = () => {
            if (stoppedRef.current) return;

            const mediaRecorder = new MediaRecorder(stream, {
              mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
                ? "audio/webm;codecs=opus"
                : "audio/webm",
            });
            mediaRecorderRef.current = mediaRecorder;
            const chunks: Blob[] = [];

            mediaRecorder.ondataavailable = (e) => {
              if (e.data.size > 0) chunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
              if (chunks.length > 0) {
                const blob = new Blob(chunks, { type: mediaRecorder.mimeType });
                // Only send if blob is meaningful (>1KB = likely has speech)
                if (blob.size > 1000) {
                  sendAudio(blob);
                }
              }
              // Start next recording cycle
              if (!stoppedRef.current) {
                startRecording();
              }
            };

            mediaRecorder.start();

            // Record in 3-second chunks
            silenceTimerRef.current = setTimeout(() => {
              if (mediaRecorder.state === "recording") {
                mediaRecorder.stop();
              }
            }, 3000);
          };

          startRecording();
        })
        .catch((err) => {
          console.error("Microphone error:", err);
          setIsListening(false);
        });
    },
    [sendAudio]
  );

  const stopListening = useCallback(() => {
    stoppedRef.current = true;
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsListening(false);
    setTranscript("");
  }, []);

  return { startListening, stopListening, isListening, transcript };
}

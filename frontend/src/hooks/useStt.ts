import { useState, useCallback, useRef } from "react";
import { useAppStore } from "@/lib/store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// VAD settings
const SILENCE_THRESHOLD = 0.015; // RMS threshold below which audio is "silence"
const SILENCE_DURATION_MS = 1200; // How long silence must last before sending
const MIN_SPEECH_DURATION_MS = 500; // Minimum speech duration to avoid noise bursts
const MAX_RECORD_DURATION_MS = 15000; // Max recording before forced send

export function useStt() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const onResultRef = useRef<((text: string) => void) | null>(null);
  const stoppedRef = useRef(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const sendAudio = useCallback(async (blob: Blob) => {
    try {
      const formData = new FormData();
      formData.append("audio", blob, "audio.webm");
      formData.append("locale", useAppStore.getState().locale);

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
  }, []);

  const startListening = useCallback(
    (onResult: (text: string) => void) => {
      onResultRef.current = onResult;
      stoppedRef.current = false;

      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          streamRef.current = stream;
          setIsListening(true);

          // Set up AudioContext + AnalyserNode for VAD
          const audioContext = new AudioContext();
          const source = audioContext.createMediaStreamSource(stream);
          const analyser = audioContext.createAnalyser();
          analyser.fftSize = 512;
          source.connect(analyser);
          audioContextRef.current = audioContext;
          analyserRef.current = analyser;

          const startRecording = () => {
            if (stoppedRef.current) return;

            const mediaRecorder = new MediaRecorder(stream, {
              mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
                ? "audio/webm;codecs=opus"
                : "audio/webm",
            });
            mediaRecorderRef.current = mediaRecorder;
            const chunks: Blob[] = [];

            let speechStartTime: number | null = null;
            let silenceStartTime: number | null = null;
            let maxTimer: ReturnType<typeof setTimeout> | null = null;

            mediaRecorder.ondataavailable = (e) => {
              if (e.data.size > 0) chunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
              if (maxTimer) clearTimeout(maxTimer);
              if (rafRef.current) cancelAnimationFrame(rafRef.current);

              if (chunks.length > 0) {
                const blob = new Blob(chunks, { type: mediaRecorder.mimeType });
                if (blob.size > 1000 && speechStartTime !== null) {
                  sendAudio(blob);
                }
              }
              // Start next recording cycle
              if (!stoppedRef.current) {
                startRecording();
              }
            };

            mediaRecorder.start();
            const recordStartTime = Date.now();

            // Force stop after max duration
            maxTimer = setTimeout(() => {
              if (mediaRecorder.state === "recording") {
                mediaRecorder.stop();
              }
            }, MAX_RECORD_DURATION_MS);

            // Monitor audio levels for VAD
            const dataArray = new Float32Array(analyser.frequencyBinCount);

            const checkAudioLevel = () => {
              if (stoppedRef.current || mediaRecorder.state !== "recording") return;

              analyser.getFloatTimeDomainData(dataArray);

              // Calculate RMS
              let sum = 0;
              for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
              }
              const rms = Math.sqrt(sum / dataArray.length);
              const now = Date.now();

              if (rms > SILENCE_THRESHOLD) {
                // Speech detected
                if (speechStartTime === null) speechStartTime = now;
                silenceStartTime = null;
              } else {
                // Silence detected
                if (speechStartTime !== null && silenceStartTime === null) {
                  silenceStartTime = now;
                }

                // If we had speech and silence lasted long enough, stop recording
                if (
                  speechStartTime !== null &&
                  silenceStartTime !== null &&
                  now - silenceStartTime >= SILENCE_DURATION_MS &&
                  now - speechStartTime >= MIN_SPEECH_DURATION_MS
                ) {
                  if (mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                  }
                  return;
                }
              }

              rafRef.current = requestAnimationFrame(checkAudioLevel);
            };

            rafRef.current = requestAnimationFrame(checkAudioLevel);
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
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setIsListening(false);
    setTranscript("");
  }, []);

  return { startListening, stopListening, isListening, transcript };
}

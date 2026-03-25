"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { useFaceWS } from "./useFaceWS";

export type KioskState = "sleeping" | "waking" | "active" | "idle";

// Read configuration from environment
const getEnv = (key: string, defaultValue: any) => {
  const value = process.env[key];
  if (value === undefined || value === '') return defaultValue;
  return value;
};

// Sleep mode configuration - HARDCODED OFF for now
const SLEEP_MODE_ENABLED = false;
const IDLE_TIMEOUT = parseInt(getEnv('NEXT_PUBLIC_KIOSK_IDLE_TIMEOUT', '20000'), 10);
const WAKE_THRESHOLD = parseInt(getEnv('NEXT_PUBLIC_KIOSK_WAKE_THRESHOLD', '3'), 10);
const SLEEP_ALLOWED_START_HOUR = getEnv('NEXT_PUBLIC_KIOSK_SLEEP_ALLOWED_START_HOUR', undefined);
const SLEEP_ALLOWED_END_HOUR = getEnv('NEXT_PUBLIC_KIOSK_SLEEP_ALLOWED_END_HOUR', undefined);
const FACE_CHECK_INTERVAL = 1500;

const NO_FACE_THRESHOLD = Math.ceil(IDLE_TIMEOUT / FACE_CHECK_INTERVAL);

function isSleepAllowedByTime(): boolean {
  if (SLEEP_ALLOWED_START_HOUR === undefined || SLEEP_ALLOWED_END_HOUR === undefined) {
    return true; // no time restriction
  }
  const start = parseInt(SLEEP_ALLOWED_START_HOUR, 10);
  const end = parseInt(SLEEP_ALLOWED_END_HOUR, 10);
  const now = new Date();
  const hour = now.getHours();
  if (start <= end) {
    return hour >= start && hour < end;
  } else {
    // overnight range, e.g., 22 to 6
    return hour >= start || hour < end;
  }
}

// Simple greeting — no auto-comments about age/expression/lookalike
// Those are available in store for AI to answer when user asks
function buildGreeting(
  locale: string,
  name: string | null,
  age: number | null,
  gender: string | null,
): { text: string; mood: string } {
  if (name) {
    if (age && age < 25) {
      const g: Record<string, string> = {
        uz: `Salom, ${name}! Yaxshi ko'rinasan! Qanday yordam bera olaman?`,
        ru: `Привет, ${name}! Рад тебя видеть! Чем помочь?`,
        en: `Hey, ${name}! Good to see you! How can I help?`,
        kr: `안녕, ${name}! 반가워! 뭘 도와줄까?`,
      };
      return { text: g[locale] || g.en, mood: "happy" };
    }
    if (age && age >= 25) {
      const g: Record<string, string> = {
        uz: `Assalomu alaykum, ${name}! Sizga qanday yordam bera olaman?`,
        ru: `Здравствуйте, ${name}! Чем могу помочь?`,
        en: `Hello, ${name}! How may I assist you?`,
        kr: `안녕하세요, ${name}님! 무엇을 도와드릴까요?`,
      };
      return { text: g[locale] || g.en, mood: "greeting" };
    }
    const g: Record<string, string> = {
      uz: `Salom, ${name}! Sizni tanidim! Qanday yordam bera olaman?`,
      ru: `Привет, ${name}! Я тебя узнал! Чем помочь?`,
      en: `Hi, ${name}! I recognized you! How can I help?`,
      kr: `안녕하세요, ${name}님! 반갑습니다! 무엇을 도와드릴까요?`,
    };
    return { text: g[locale] || g.en, mood: "greeting" };
  }

  if (age && age < 25) {
    const g: Record<string, string> = {
      uz: "Salom! Men seni tanimadim. Ismingni harf-harf ayt!",
      ru: "Привет! Я тебя не узнал. Произнеси своё имя по буквам!",
      en: "Hey there! I don't recognize you. Spell your name for me!",
      kr: "안녕! 처음 보는 얼굴이야. 이름을 한 글자씩 말해줘!",
    };
    return { text: g[locale] || g.en, mood: "curious" };
  }
  if (age && age >= 25) {
    const g: Record<string, string> = {
      uz: "Assalomu alaykum! Sizni tanimadim. Iltimos, ismingizni ayting.",
      ru: "Здравствуйте! Я вас не узнал. Пожалуйста, назовите ваше имя по буквам.",
      en: "Hello! I don't recognize you. Could you spell your name?",
      kr: "안녕하세요! 처음 뵙겠습니다. 성함을 한 글자씩 말씀해주세요.",
    };
    return { text: g[locale] || g.en, mood: "curious" };
  }
  const g: Record<string, string> = {
    uz: "Salom! Men sizni tanimadim. Ismingizni harf-harf ayting!",
    ru: "Привет! Я тебя не узнал. Произнеси своё имя по буквам!",
    en: "Hi! I don't recognize you. Please spell your name!",
    kr: "안녕하세요! 처음 뵙겠습니다. 이름을 한 글자씩 말해주세요!",
  };
  return { text: g[locale] || g.en, mood: "curious" };
}

export function useKioskMode() {
  const [state, setState] = useState<KioskState>("active");
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const presenceCountRef = useRef(0);
  const noFaceCountRef = useRef(0);
  const initialGreetDoneRef = useRef(false);

  const locale = useAppStore((s) => s.locale);
  const clearMessages = useAppStore((s) => s.clearMessages);
  const setMood = useAppStore((s) => s.setMood);
  const addMessage = useAppStore((s) => s.addMessage);
  const setUserName = useAppStore((s) => s.setUserName);
  const setWaitingForName = useAppStore((s) => s.setWaitingForName);

  // Face analysis via WebSocket → InsightFace backend
  const { lastResult, registerFace } = useFaceWS(videoRef);

  // Start camera
  useEffect(() => {
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: "user" },
        });
        setCameraStream(stream);
      } catch {
        console.warn("Camera not available");
      }
    })();

    return () => {
      cameraStream?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Assign stream to video
  useEffect(() => {
    if (videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
      videoRef.current.play().catch(() => {});
    }
  }, [cameraStream]);

  const markActive = useCallback(() => {
    if (state === "idle" || state === "sleeping") {
      setState("active");
    }
  }, [state]);

  // Wake with greeting
  const wake = useCallback(() => {
    setState("waking");
    setMood("greeting");
    clearMessages();

    const { name, age, gender } = lastResult.current;
    const greeting = buildGreeting(locale, name, age, gender);

    if (name) {
      setUserName(name);
      setWaitingForName(false);
    } else {
      setWaitingForName(true);
    }

    setMood(greeting.mood as any);
    addMessage({ role: "assistant", content: greeting.text, mood: greeting.mood as any });

    setTimeout(() => setState("active"), 500);
  }, [locale, setMood, clearMessages, addMessage, setUserName, setWaitingForName, lastResult]);

  // Initial greeting on first load
  useEffect(() => {
    if (initialGreetDoneRef.current || !cameraStream) return;

    const tryInitialGreet = async () => {
      // Wait for camera + first WS result
      for (let i = 0; i < 10; i++) {
        await new Promise((r) => setTimeout(r, 500));
        if (videoRef.current && videoRef.current.readyState >= 2) break;
      }
      // Extra wait for first WS response
      await new Promise((r) => setTimeout(r, 2000));

      if (initialGreetDoneRef.current) return;
      initialGreetDoneRef.current = true;

      const { name, age, gender } = lastResult.current;
      const greeting = buildGreeting(locale, name, age, gender);

      if (name) {
        setUserName(name);
        setWaitingForName(false);
      } else {
        setWaitingForName(true);
      }

      setMood(greeting.mood as any);
      addMessage({ role: "assistant", content: greeting.text, mood: greeting.mood as any });
    };

    tryInitialGreet();
  }, [cameraStream, locale, setMood, addMessage, setUserName, setWaitingForName, lastResult]);

  // Activity tracking
  useEffect(() => {
    const events = ["mousedown", "touchstart", "keydown", "mousemove"];
    events.forEach((e) => window.addEventListener(e, markActive));
    return () => events.forEach((e) => window.removeEventListener(e, markActive));
  }, [markActive]);

  // State machine — sleep when no face AND time window allows, wake when face appears or time ends
  useEffect(() => {
    const interval = setInterval(() => {
      const faceDetected = lastResult.current.detected;

      if (state === "active") {
        if (faceDetected) {
          noFaceCountRef.current = 0;
        } else {
          noFaceCountRef.current += 1;
          if (noFaceCountRef.current >= NO_FACE_THRESHOLD) {
            noFaceCountRef.current = 0;
            // Only sleep if enabled AND time window allows
            if (SLEEP_MODE_ENABLED && isSleepAllowedByTime()) {
              setState("sleeping");
              clearMessages();
              setMood("resting");
              presenceCountRef.current = 0;
            }
          }
        }
        return;
      }

      if (state === "sleeping") {
        // Wake if time window expired (even without face)
        if (SLEEP_MODE_ENABLED && !isSleepAllowedByTime()) {
          presenceCountRef.current = 0;
          noFaceCountRef.current = 0;
          setState("active");
          return;
        }

        if (faceDetected) {
          presenceCountRef.current += 1;
          if (presenceCountRef.current >= WAKE_THRESHOLD) {
            presenceCountRef.current = 0;
            noFaceCountRef.current = 0;
            wake();
          }
        } else {
          presenceCountRef.current = 0;
        }
      }
    }, FACE_CHECK_INTERVAL);

    return () => clearInterval(interval);
  }, [state, wake, clearMessages, setMood, lastResult]);

  return { state, videoRef, markActive, registerFace };
}

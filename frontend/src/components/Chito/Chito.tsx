"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { useAppStore } from "@/lib/store";
import type { MascotMood } from "@/lib/store";

const BLINK_FRAMES = [
  "/mascot/idle.png",
  "/mascot/blink_half.png",
  "/mascot/blink_full.png",
  "/mascot/blink_half.png",
  "/mascot/idle.png",
];

const TALK_FRAMES = [
  "/mascot/idle.png",
  "/mascot/talk_a.png",
  "/mascot/talk_b.png",
  "/mascot/talk_a.png",
];

const ALL_SPRITES = [
  "/mascot/idle.png",
  "/mascot/blink_half.png",
  "/mascot/blink_full.png",
  "/mascot/talk_a.png",
  "/mascot/talk_b.png",
];

function usePreloadImages() {
  const done = useRef(false);
  useEffect(() => {
    if (done.current) return;
    done.current = true;
    ALL_SPRITES.forEach((src) => {
      const img = new window.Image();
      img.src = src;
    });
  }, []);
}

function useBlinkAnimation(enabled: boolean) {
  const [frame, setFrame] = useState(0);
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    if (!enabled) { setFrame(0); setIsBlinking(false); return; }

    const scheduleNextBlink = () => {
      const delay = 2000 + Math.random() * 4000;
      return setTimeout(() => setIsBlinking(true), delay);
    };

    let timer = scheduleNextBlink();
    return () => clearTimeout(timer);
  }, [enabled, isBlinking]);

  useEffect(() => {
    if (!isBlinking) return;
    let i = 0;
    setFrame(0);
    const interval = setInterval(() => {
      i++;
      if (i >= BLINK_FRAMES.length) {
        setIsBlinking(false);
        setFrame(0);
        clearInterval(interval);
      } else {
        setFrame(i);
      }
    }, 80);
    return () => clearInterval(interval);
  }, [isBlinking]);

  return isBlinking ? BLINK_FRAMES[frame] : null;
}

function useTalkAnimation(enabled: boolean) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (!enabled) { setFrame(0); return; }
    const interval = setInterval(() => {
      setFrame((f) => (f + 1) % TALK_FRAMES.length);
    }, 150);
    return () => clearInterval(interval);
  }, [enabled]);

  return enabled ? TALK_FRAMES[frame] : null;
}

export default function Uzumchi() {
  usePreloadImages();

  const mood = useAppStore((s) => s.mood);
  const isLoading = useAppStore((s) => s.isLoading);

  const isSpeaking = useAppStore((s) => s.isSpeaking);
  const isTalking = isSpeaking || mood === "talking";
  const isThinking = isLoading;

  const talkSprite = useTalkAnimation(isTalking && !isThinking);
  const blinkSprite = useBlinkAnimation(!isTalking && !isThinking);

  let sprite: string;
  if (isThinking) {
    sprite = "/mascot/idle.png";
  } else if (talkSprite) {
    sprite = talkSprite;
  } else if (blinkSprite) {
    sprite = blinkSprite;
  } else {
    sprite = "/mascot/idle.png";
  }

  const floatAnimation = { y: [0, -6, 0] };
  const floatTransition = { duration: 3, repeat: Infinity, ease: "easeInOut" as const };

  return (
    <div className="relative flex items-center justify-center w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80 mt-8">
      {/* Thinking dots above mascot */}
      {isThinking && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-3 h-3 md:w-4 md:h-4 rounded-full bg-purple-400"
              animate={{ y: [0, -8, 0], opacity: [0.4, 1, 0.4] }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: "easeInOut",
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      )}
      <motion.div
        animate={floatAnimation}
        transition={floatTransition}
        className="relative w-full h-full"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={sprite}
          alt="Uzumchi"
          className="absolute inset-0 w-full h-full object-contain drop-shadow-xl"
        />
      </motion.div>
    </div>
  );
}

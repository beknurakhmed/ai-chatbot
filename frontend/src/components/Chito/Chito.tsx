"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { useAppStore } from "@/lib/store";

// Breathing cycle: 1→2→3→4→3→2→1 with per-frame delays (ms)
const SLEEP_SEQUENCE = [
  { src: "/chito/sleep_1.png", delay: 2500 }, // resting, mouth closed — long pause
  { src: "/chito/sleep_2.png", delay: 600 },  // mouth starts opening
  { src: "/chito/sleep_3.png", delay: 500 },  // mouth open — exhale
  { src: "/chito/sleep_4.png", delay: 700 },  // mouth wider — peak exhale
  { src: "/chito/sleep_3.png", delay: 500 },  // closing back
  { src: "/chito/sleep_2.png", delay: 600 },  // almost closed
];
// total cycle ~5.4s

const THINKING_FRAMES = [
  "/chito/thinking_1.png",
  "/chito/thinking_2.png",
  "/chito/thinking_3.png",
  "/chito/thinking_4.png",
];

// Preload all images on mount
function usePreloadImages() {
  const done = useRef(false);
  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const srcs = ["/chito/chito_idle.png", ...SLEEP_SEQUENCE.map((f) => f.src), ...THINKING_FRAMES,
      "/chito/layers/eyes_closed.png", "/chito/layers/mouth_open_old.png", "/chito/layers/mouth_half_old.png"];
    srcs.forEach((src) => {
      const img = new window.Image();
      img.src = src;
    });
  }, []);
}

export default function Chito() {
  usePreloadImages();

  const mood = useAppStore((s) => s.mood);
  const isLoading = useAppStore((s) => s.isLoading);
  const [blink, setBlink] = useState(false);
  const [mouthState, setMouthState] = useState<"closed" | "half" | "open">("closed");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);

  // Blink every 1.5-3.5 seconds
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;
    function doBlink() {
      timeout = setTimeout(() => {
        setBlink(true);
        setTimeout(() => setBlink(false), 150);
        doBlink();
      }, 1500 + Math.random() * 2000);
    }
    doBlink();
    return () => clearTimeout(timeout);
  }, []);

  // Frame animation for sleeping and thinking
  const frameRef = useRef(0);

  useEffect(() => {
    if (mood !== "resting" && mood !== "thinking") {
      frameRef.current = 0;
      setFrameIndex(0);
      return;
    }

    let timerId: ReturnType<typeof setTimeout>;
    let stopped = false;

    function tick() {
      if (stopped) return;
      const seq = mood === "resting" ? SLEEP_SEQUENCE : THINKING_FRAMES;
      const next = (frameRef.current + 1) % seq.length;
      frameRef.current = next;
      setFrameIndex(next);

      const delay = mood === "resting"
        ? SLEEP_SEQUENCE[next].delay
        : 1200;
      timerId = setTimeout(tick, delay);
    }

    const firstDelay = mood === "resting" ? SLEEP_SEQUENCE[0].delay : 1200;
    timerId = setTimeout(tick, firstDelay);

    return () => {
      stopped = true;
      clearTimeout(timerId);
    };
  }, [mood]);

  // Lip-sync: watch for audio elements playing
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const mouthCycle: Array<"closed" | "half" | "open"> = ["closed", "open", "half", "open", "closed", "half"];
    let mouthIdx = 0;

    function checkAudio() {
      const audios = document.querySelectorAll("audio");
      let anyPlaying = false;
      audios.forEach((a) => {
        if (!a.paused && !a.ended) anyPlaying = true;
      });

      setIsSpeaking(anyPlaying);

      if (anyPlaying && !interval) {
        interval = setInterval(() => {
          mouthIdx = (mouthIdx + 1) % mouthCycle.length;
          setMouthState(mouthCycle[mouthIdx]);
        }, 120);
      } else if (!anyPlaying && interval) {
        clearInterval(interval);
        interval = null;
        setMouthState("closed");
      }
    }

    const pollId = setInterval(checkAudio, 100);
    return () => {
      clearInterval(pollId);
      if (interval) clearInterval(interval);
    };
  }, []);

  // Determine current sprite
  let sprite: string;
  if (mood === "resting") {
    sprite = SLEEP_SEQUENCE[frameIndex]?.src || SLEEP_SEQUENCE[0].src;
  } else if (mood === "thinking" || isLoading) {
    sprite = THINKING_FRAMES[frameIndex] || THINKING_FRAMES[0];
  } else {
    sprite = "/chito/chito_idle.png";
  }

  const showOverlays = sprite === "/chito/chito_idle.png";

  return (
    <div className="relative flex items-center justify-center w-32 h-32 sm:w-48 sm:h-48 md:w-64 md:h-64 lg:w-80 lg:h-80">
      <motion.div
        animate={{ y: [0, -6, 0] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className="relative w-full h-full"
      >
        {/* Single img tag — just swap src, no flicker */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={sprite}
          alt="Chito"
          className="absolute inset-0 w-full h-full object-contain drop-shadow-xl"
        />

        {/* Eyes closed overlay */}
        {showOverlays && blink && !isSpeaking && (
          <Image
            src="/chito/layers/eyes_closed.png"
            alt=""
            fill
            className="object-contain pointer-events-none"
            sizes="(max-width: 768px) 192px, (max-width: 1024px) 256px, 320px"
          />
        )}

        {/* Mouth open overlay */}
        {showOverlays && isSpeaking && mouthState === "open" && (
          <Image
            src="/chito/layers/mouth_open_old.png"
            alt=""
            fill
            className="object-contain pointer-events-none"
            sizes="(max-width: 768px) 192px, (max-width: 1024px) 256px, 320px"
          />
        )}

        {/* Mouth half overlay */}
        {showOverlays && isSpeaking && mouthState === "half" && (
          <Image
            src="/chito/layers/mouth_half_old.png"
            alt=""
            fill
            className="object-contain pointer-events-none"
            sizes="(max-width: 768px) 192px, (max-width: 1024px) 256px, 320px"
          />
        )}
      </motion.div>
    </div>
  );
}

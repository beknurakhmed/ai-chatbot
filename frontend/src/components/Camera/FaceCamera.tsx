"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useFaceDetection } from "@/hooks/useFaceDetection";
import { useAppStore } from "@/lib/store";

export default function FaceCamera() {
  const { videoRef, isActive, detectedName, startCamera, stopCamera, registerFace } =
    useFaceDetection();
  const locale = useAppStore((s) => s.locale);
  const [showRegister, setShowRegister] = useState(false);
  const [regName, setRegName] = useState("");
  const [regStatus, setRegStatus] = useState<"idle" | "success" | "fail">("idle");

  const labels = {
    uz: { start: "Kamera", register: "Ro'yxatdan o'tish", name: "Ismingiz", save: "Saqlash", hi: "Salom", detected: "Aniqlandi" },
    ru: { start: "Камера", register: "Регистрация", name: "Ваше имя", save: "Сохранить", hi: "Привет", detected: "Распознан" },
    en: { start: "Camera", register: "Register", name: "Your name", save: "Save", hi: "Hello", detected: "Detected" },
    kr: { start: "카메라", register: "등록", name: "이름", save: "저장", hi: "안녕", detected: "감지됨" },
  };
  const l = labels[locale as keyof typeof labels] || labels.en;

  async function handleRegister() {
    if (!regName.trim()) return;
    const ok = await registerFace(regName.trim());
    setRegStatus(ok ? "success" : "fail");
    if (ok) {
      setShowRegister(false);
      setRegName("");
      setTimeout(() => setRegStatus("idle"), 3000);
    }
  }

  return (
    <div className="relative">
      {/* Camera toggle button */}
      {!isActive ? (
        <button
          onClick={startCamera}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium
                     bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
          {l.start}
        </button>
      ) : (
        <div className="flex items-center gap-2">
          {detectedName && (
            <span className="text-sm text-green-600 font-medium">
              {l.hi}, {detectedName}!
            </span>
          )}
          {!detectedName && (
            <button
              onClick={() => setShowRegister(!showRegister)}
              className="px-3 py-2 rounded-xl text-sm font-medium bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
            >
              {l.register}
            </button>
          )}
          <button
            onClick={stopCamera}
            className="px-3 py-2 rounded-xl text-sm font-medium bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
          >
            ✕
          </button>
        </div>
      )}

      {/* Hidden video element */}
      <video
        ref={videoRef}
        className="hidden"
        playsInline
        muted
      />

      {/* Registration popup */}
      <AnimatePresence>
        {showRegister && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-12 right-0 bg-white rounded-xl shadow-lg border border-blue-100 p-4 z-50 w-64"
          >
            <p className="text-sm text-gray-600 mb-2">{l.name}:</p>
            <input
              type="text"
              value={regName}
              onChange={(e) => setRegName(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm mb-2
                         focus:outline-none focus:border-blue-400"
              placeholder="Beknur"
            />
            <button
              onClick={handleRegister}
              className="w-full bg-blue-500 text-white rounded-lg py-2 text-sm font-medium
                         hover:bg-blue-600 transition-colors"
            >
              {l.save}
            </button>
            {regStatus === "fail" && (
              <p className="text-xs text-red-500 mt-1">No face detected. Look at camera.</p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

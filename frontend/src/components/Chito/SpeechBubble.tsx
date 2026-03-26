"use client";

import { motion, AnimatePresence } from "framer-motion";

interface SpeechBubbleProps {
  text: string;
  isVisible: boolean;
  isTyping?: boolean;
}

export default function SpeechBubble({ text, isVisible, isTyping }: SpeechBubbleProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          transition={{ duration: 0.3 }}
          className="relative max-w-md mx-auto"
        >
          <div className="bg-white rounded-2xl px-6 py-4 shadow-lg border-2 border-blue-200">
            <p className="text-gray-800 text-lg md:text-xl text-center leading-relaxed">
              {text}
              {isTyping && (
                <span className="inline-block w-[3px] h-[1.1em] bg-blue-400 ml-0.5 align-middle animate-pulse" />
              )}
            </p>
          </div>
          {/* Triangle pointer */}
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-b-[12px] border-b-white drop-shadow-sm" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

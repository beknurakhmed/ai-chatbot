"use client";

import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { motion, AnimatePresence } from "framer-motion";

const LINKS = [
  { label: "GitHub", url: "https://github.com/beknurakhmed", icon: "M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" },
  { label: "LinkedIn", url: "https://www.linkedin.com/in/beknur-akhmedov-6716292b4/", icon: "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" },
  { label: "Website", url: "https://www.beknurdev.uz/", icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" },
];

export default function AuthorFooter({ inline }: { inline?: boolean }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={inline
          ? "text-[10px] text-gray-400 hover:text-blue-500 transition-colors py-0.5 font-medium"
          : "fixed z-40 bottom-4 right-6 bg-white/90 backdrop-blur-sm border border-gray-200 shadow-lg rounded-full px-5 py-2.5 text-sm text-gray-500 hover:text-blue-600 hover:border-blue-300 font-medium transition-all hover:shadow-xl"
        }
      >
        {inline
          ? <>by <b>Akhmedov Beknur</b> | ECE</>
          : <>Developed by <span className="font-bold text-gray-800">Akhmedov Beknur</span> <span className="text-gray-400">| ECE</span></>
        }
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-end md:items-center justify-center z-50"
            onClick={() => setOpen(false)}
          >
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-t-3xl md:rounded-3xl shadow-2xl w-full max-w-sm md:mx-4 overflow-hidden"
            >
              {/* Header */}
              <div className="bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 px-6 py-6 text-white text-center relative">
                <div className="w-20 h-20 bg-white/20 rounded-full mx-auto mb-3 flex items-center justify-center text-3xl font-bold backdrop-blur-sm border-2 border-white/30">
                  BA
                </div>
                <h2 className="text-xl font-bold">Akhmedov Beknur</h2>
                <p className="text-blue-100 text-sm mt-1.5">Electrical & Computer Engineering</p>
                <p className="text-blue-200 text-xs mt-1">Ajou University in Tashkent</p>
              </div>

              {/* Links with QR */}
              <div className="p-5 space-y-4">
                {LINKS.map((link) => (
                  <div key={link.label} className="flex items-center gap-4 p-3 rounded-2xl bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="flex-shrink-0 bg-white rounded-xl p-1.5 shadow-sm">
                      <QRCodeSVG value={link.url} size={60} level="L" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <svg className="w-5 h-5 text-gray-700 flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                          <path d={link.icon} />
                        </svg>
                        <span className="text-base font-semibold text-gray-800">{link.label}</span>
                      </div>
                      <p className="text-xs text-gray-400 truncate mt-1">{link.url}</p>
                      <p className="text-[10px] text-blue-500 mt-0.5">Scan QR to open</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Close */}
              <div className="px-5 pb-5">
                <button
                  onClick={() => setOpen(false)}
                  className="w-full py-3 text-sm font-semibold text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-2xl transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

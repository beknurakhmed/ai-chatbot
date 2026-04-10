import { create } from "zustand";
import type { Locale } from "@/i18n";

export type MascotMood =
  | "idle"
  | "greeting"
  | "explaining"
  | "thinking"
  | "happy"
  | "sad"
  | "warning"
  | "celebrating"
  | "curious"
  | "waving"
  | "presenting"
  | "talking"
  | "smiling"
  | "winking";

export interface OnboardingTaskData {
  id: number;
  title: string;
  description: string | null;
  category: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  mood?: MascotMood;
  onboarding?: OnboardingTaskData[];
  timestamp: number;
}

interface AppState {
  locale: Locale;
  setLocale: (locale: Locale) => void;

  mood: MascotMood;
  setMood: (mood: MascotMood) => void;

  messages: Message[];
  addMessage: (msg: Omit<Message, "id" | "timestamp">) => void;
  clearMessages: () => void;

  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  employeeName: string | null;
  setEmployeeName: (name: string | null) => void;

  isSpeaking: boolean;
  setIsSpeaking: (v: boolean) => void;

  ttsEnabled: boolean;
  setTtsEnabled: (v: boolean) => void;

  ttsPreparingId: string | null;
  setTtsPreparingId: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  locale: "ru",
  setLocale: (locale) => set({ locale }),

  mood: "idle",
  setMood: (mood) => set({ mood }),

  messages: [],
  addMessage: (msg) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...msg, id: crypto.randomUUID(), timestamp: Date.now() },
      ],
    })),
  clearMessages: () => set({ messages: [] }),

  isLoading: false,
  setLoading: (isLoading) => set({ isLoading }),

  employeeName: null,
  setEmployeeName: (employeeName) => set({ employeeName }),

  isSpeaking: false,
  setIsSpeaking: (isSpeaking) => set({ isSpeaking }),

  ttsEnabled: true,
  setTtsEnabled: (ttsEnabled) => set({ ttsEnabled }),

  ttsPreparingId: null,
  setTtsPreparingId: (ttsPreparingId) => set({ ttsPreparingId }),
}));

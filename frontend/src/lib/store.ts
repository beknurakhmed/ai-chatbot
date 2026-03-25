import { create } from "zustand";
import type { Locale } from "@/i18n";

export type ChitoMood =
  | "idle"
  | "greeting"
  | "explaining"
  | "thinking"
  | "happy"
  | "sad"
  | "warning"
  | "studying"
  | "working"
  | "celebrating"
  | "curious"
  | "wizard"
  | "birthday"
  | "christmas"
  | "holiday"
  | "resting"
  | "laptop"
  | "bottle"
  | "soccer";

export interface TimetableLesson {
  day: string;
  period: string;
  time: string;
  subject: string;
  teacher: string;
  room: string;
}

export interface StaffMember {
  name: string;
  position: string;
  photo: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  mood?: ChitoMood;
  timetable?: { group: string; lessons: TimetableLesson[] };
  staff?: StaffMember[];
  map?: boolean;
  timestamp: number;
}

export interface FaceAttributes {
  age: number | null;
  gender: string | null;
  expression: string | null;
  expressionScore: number;
  lookalike?: string | null;
}

interface AppState {
  locale: Locale;
  setLocale: (locale: Locale) => void;

  mood: ChitoMood;
  setMood: (mood: ChitoMood) => void;

  faceAttributes: FaceAttributes;
  setFaceAttributes: (attrs: FaceAttributes) => void;

  messages: Message[];
  addMessage: (msg: Omit<Message, "id" | "timestamp">) => void;
  clearMessages: () => void;

  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  userName: string | null;
  setUserName: (name: string | null) => void;

  waitingForName: boolean;
  setWaitingForName: (v: boolean) => void;

  pendingName: string | null;
  setPendingName: (name: string | null) => void;

  waitingForConfirmation: boolean;
  setWaitingForConfirmation: (v: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  locale: "en",
  setLocale: (locale) => set({ locale }),

  mood: "idle",
  setMood: (mood) => set({ mood }),

  faceAttributes: { age: null, gender: null, expression: null, expressionScore: 0 },
  setFaceAttributes: (faceAttributes) => set({ faceAttributes }),

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

  userName: null,
  setUserName: (userName) => set({ userName }),

  waitingForName: false,
  setWaitingForName: (waitingForName) => set({ waitingForName }),

  pendingName: null,
  setPendingName: (pendingName) => set({ pendingName }),

  waitingForConfirmation: false,
  setWaitingForConfirmation: (waitingForConfirmation) => set({ waitingForConfirmation }),
}));

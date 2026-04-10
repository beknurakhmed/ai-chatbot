import { useAppStore } from "@/lib/store";
import { sendMessage, getTtsUrl } from "@/lib/api";
import { t } from "@/i18n";
import type { MascotMood } from "@/lib/store";

let currentAudio: HTMLAudioElement | null = null;

function stopCurrentAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.src = "";
    currentAudio = null;
  }
}

async function playTts(text: string, locale: string): Promise<void> {
  const { setIsSpeaking, setMood, ttsEnabled } = useAppStore.getState();
  if (!ttsEnabled) return;

  stopCurrentAudio();

  const audio = new Audio();
  currentAudio = audio;

  return new Promise<void>((resolve) => {
    audio.oncanplaythrough = () => {
      resolve();
      audio.play().catch(() => {
        setIsSpeaking(false);
        setMood("idle");
      });
    };
    audio.onplay = () => {
      setIsSpeaking(true);
      setMood("talking");
    };
    audio.onended = () => {
      setIsSpeaking(false);
      setMood("idle");
      currentAudio = null;
    };
    audio.onerror = () => {
      setIsSpeaking(false);
      setMood("idle");
      currentAudio = null;
      resolve();
    };
    audio.src = getTtsUrl(text, locale);
  });
}

export function useChat() {
  const locale = useAppStore((s) => s.locale);
  const messages = useAppStore((s) => s.messages);
  const addMessage = useAppStore((s) => s.addMessage);
  const setLoading = useAppStore((s) => s.setLoading);
  const setMood = useAppStore((s) => s.setMood);
  const isLoading = useAppStore((s) => s.isLoading);
  const employeeName = useAppStore((s) => s.employeeName);

  async function send(text: string): Promise<string | null> {
    if (!text.trim() || isLoading) return null;

    stopCurrentAudio();
    addMessage({ role: "user", content: text });
    setLoading(true);
    setMood("thinking");

    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const data = await sendMessage(text, locale, history, employeeName);
      const mood = (data.mood || "explaining") as MascotMood;

      const { ttsEnabled } = useAppStore.getState();
      if (ttsEnabled) {
        // Wait for TTS to be ready, then show text + play audio together
        await playTts(data.reply, locale);
      }

      setMood(mood);
      addMessage({
        role: "assistant",
        content: data.reply,
        mood,
        onboarding: data.onboarding || undefined,
      });
      return data.reply;
    } catch {
      setMood("sad");
      const errMsg = t(locale, "chat.error");
      addMessage({ role: "assistant", content: errMsg, mood: "sad" });
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { send, isLoading };
}

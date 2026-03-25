import { useAppStore } from "@/lib/store";
import { sendMessage } from "@/lib/api";
import { t } from "@/i18n";
import type { ChitoMood } from "@/lib/store";

export function useChat() {
  const locale = useAppStore((s) => s.locale);
  const messages = useAppStore((s) => s.messages);
  const addMessage = useAppStore((s) => s.addMessage);
  const setLoading = useAppStore((s) => s.setLoading);
  const setMood = useAppStore((s) => s.setMood);
  const isLoading = useAppStore((s) => s.isLoading);
  const userName = useAppStore((s) => s.userName);
  const faceAttributes = useAppStore((s) => s.faceAttributes);

  async function send(text: string): Promise<string | null> {
    if (!text.trim() || isLoading) return null;

    addMessage({ role: "user", content: text });
    setLoading(true);
    setMood("thinking");

    // Build history from existing messages
    const history = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const data = await sendMessage(text, locale, history, userName, faceAttributes);
      const mood = (data.mood || "explaining") as ChitoMood;
      setMood(mood);
      addMessage({
        role: "assistant",
        content: data.reply,
        mood,
        timetable: data.timetable || undefined,
        staff: data.staff || undefined,
        map: data.map || undefined,
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

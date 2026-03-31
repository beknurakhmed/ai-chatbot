const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface HistoryMsg {
  role: string;
  content: string;
}

export async function sendMessage(
  message: string,
  locale: string,
  history: HistoryMsg[] = [],
  userName?: string | null,
  faceAttributes?: { age: number | null; gender: string | null; expression: string | null; expressionScore: number } | null,
): Promise<{
  reply: string;
  mood: string;
  timetable?: { group: string; lessons: Array<{ day: string; period: string; time: string; subject: string; teacher: string; room: string }> };
  staff?: Array<{ name: string; position: string; photo: string }>;
  news?: Array<{ title: string; url: string; date: string }>;
  map?: boolean;
}> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      locale,
      history,
      user_name: userName || undefined,
      face_attributes: faceAttributes?.age ? faceAttributes : undefined,
    }),
  });

  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export function getTtsUrl(text: string, locale: string): string {
  return `${API_BASE}/api/tts?text=${encodeURIComponent(text)}&locale=${locale}`;
}

export async function recognizeFace(
  imageData: string
): Promise<{ name: string | null; confidence: number }> {
  const res = await fetch(`${API_BASE}/api/face/recognize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: imageData }),
  });

  if (!res.ok) throw new Error("Face recognition failed");
  return res.json();
}

export async function saveFaceToBackend(
  name: string,
  descriptor: number[]
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/face/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, descriptor }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.ok;
  } catch {
    return false;
  }
}

export interface BuildingData {
  num: number;
  name: string;
  desc: string;
  color: string;
}

export async function fetchBuildings(): Promise<BuildingData[]> {
  try {
    const res = await fetch(`${API_BASE}/api/buildings`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function loadFacesFromBackend(): Promise<
  Array<{ name: string; descriptor: number[] }>
> {
  try {
    const res = await fetch(`${API_BASE}/api/face/list`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.faces || [];
  } catch {
    return [];
  }
}

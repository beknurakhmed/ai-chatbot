export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Token stored in localStorage
export function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("admin_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("admin_token", token);
}

export function clearToken() {
  localStorage.removeItem("admin_token");
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// --- Knowledge ---
export interface KnowledgeEntry {
  id: number;
  category: string;
  title: string;
  content: string;
  language: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export const getKnowledge = () => apiFetch<KnowledgeEntry[]>("/admin/knowledge");
export const createKnowledge = (data: Omit<KnowledgeEntry, "id" | "created_at" | "updated_at">) =>
  apiFetch<KnowledgeEntry>("/admin/knowledge", { method: "POST", body: JSON.stringify(data) });
export const updateKnowledge = (id: number, data: Omit<KnowledgeEntry, "id" | "created_at" | "updated_at">) =>
  apiFetch<KnowledgeEntry>(`/admin/knowledge/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteKnowledge = (id: number) =>
  apiFetch<void>(`/admin/knowledge/${id}`, { method: "DELETE" });
export const refreshKnowledgeCache = () =>
  apiFetch<{ status: string }>("/admin/knowledge/refresh-cache", { method: "POST" });

// --- Keywords ---
export interface Keyword {
  id: number;
  keyword: string;
  intent: string;
  language: string;
  is_active: boolean;
  created_at?: string;
}

export const getKeywords = () => apiFetch<Keyword[]>("/admin/keywords");
export const createKeyword = (data: Omit<Keyword, "id" | "created_at">) =>
  apiFetch<Keyword>("/admin/keywords", { method: "POST", body: JSON.stringify(data) });
export const updateKeyword = (id: number, data: Omit<Keyword, "id" | "created_at">) =>
  apiFetch<Keyword>(`/admin/keywords/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteKeyword = (id: number) =>
  apiFetch<void>(`/admin/keywords/${id}`, { method: "DELETE" });

// --- News ---
export interface NewsItem {
  id: number;
  external_id?: number;
  title: string;
  content?: string;
  url?: string;
  image_url?: string;
  published_at?: string;
  is_active: boolean;
  created_at?: string;
}

export const getNews = () => apiFetch<NewsItem[]>("/admin/news");
export const createNews = (data: Omit<NewsItem, "id" | "created_at">) =>
  apiFetch<NewsItem>("/admin/news", { method: "POST", body: JSON.stringify(data) });
export const updateNews = (id: number, data: Omit<NewsItem, "id" | "created_at">) =>
  apiFetch<NewsItem>(`/admin/news/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteNews = (id: number) =>
  apiFetch<void>(`/admin/news/${id}`, { method: "DELETE" });
export const refreshNews = () =>
  apiFetch<{ added: number; fetched: number }>("/admin/news/refresh", { method: "POST" });

// --- Staff ---
export interface StaffMember {
  id: number;
  name: string;
  position?: string;
  photo?: string;
  category?: string;
  is_active: boolean;
}

export const getStaff = () => apiFetch<StaffMember[]>("/admin/staff");
export const createStaff = (data: Omit<StaffMember, "id">) =>
  apiFetch<StaffMember>("/admin/staff", { method: "POST", body: JSON.stringify(data) });
export const updateStaff = (id: number, data: Omit<StaffMember, "id">) =>
  apiFetch<StaffMember>(`/admin/staff/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteStaff = (id: number) =>
  apiFetch<void>(`/admin/staff/${id}`, { method: "DELETE" });
export const refreshStaff = () =>
  apiFetch<{ count: number; updated: string }>("/admin/staff/refresh", { method: "POST" });

// --- Timetable ---
export interface TimetableEntry {
  id: number;
  group: string;
  day: string;
  period: string;
  time_str: string;
  subject: string;
  teacher?: string;
  room?: string;
  is_active: boolean;
}

export const getTimetable = () => apiFetch<TimetableEntry[]>("/admin/timetable");
export const createTimetable = (data: Omit<TimetableEntry, "id">) =>
  apiFetch<TimetableEntry>("/admin/timetable", { method: "POST", body: JSON.stringify(data) });
export const updateTimetable = (id: number, data: Omit<TimetableEntry, "id">) =>
  apiFetch<TimetableEntry>(`/admin/timetable/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteTimetable = (id: number) =>
  apiFetch<void>(`/admin/timetable/${id}`, { method: "DELETE" });
export const refreshTimetable = () =>
  apiFetch<{ classes: number; entries_saved: number; updated: string }>("/admin/timetable/refresh", { method: "POST" });

// --- Buildings ---
export interface BuildingEntry {
  id: number;
  num: number;
  name: string;
  description?: string;
  photo?: string;
  color: string;
  is_active: boolean;
}

export const getBuildings = () => apiFetch<BuildingEntry[]>("/admin/buildings");
export const createBuilding = (data: Omit<BuildingEntry, "id">) =>
  apiFetch<BuildingEntry>("/admin/buildings", { method: "POST", body: JSON.stringify(data) });
export const updateBuilding = (id: number, data: Omit<BuildingEntry, "id">) =>
  apiFetch<BuildingEntry>(`/admin/buildings/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteBuilding = (id: number) =>
  apiFetch<void>(`/admin/buildings/${id}`, { method: "DELETE" });

// --- Rooms ---
export interface RoomEntry {
  id: number;
  name: string;
  block?: string;
  floor?: number;
  capacity?: number;
  is_active: boolean;
}

export const getRooms = () => apiFetch<RoomEntry[]>("/admin/rooms");
export const createRoom = (data: Omit<RoomEntry, "id">) =>
  apiFetch<RoomEntry>("/admin/rooms", { method: "POST", body: JSON.stringify(data) });
export const updateRoom = (id: number, data: Omit<RoomEntry, "id">) =>
  apiFetch<RoomEntry>(`/admin/rooms/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteRoom = (id: number) =>
  apiFetch<void>(`/admin/rooms/${id}`, { method: "DELETE" });
export const syncRooms = () =>
  apiFetch<{ synced: number; total_timetable_rooms: number; existing: number }>("/admin/rooms/sync", { method: "POST" });

// --- Logs ---
export interface LogEntry {
  id: number;
  user_name?: string;
  message?: string;
  reply?: string;
  locale?: string;
  mood?: string;
  created_at?: string;
}

export const getLogs = () => apiFetch<LogEntry[]>("/admin/logs");

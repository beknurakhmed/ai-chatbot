export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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



export interface OnboardingTask {
  id: number;
  title: string;
  description?: string;
  category: string;
  order_num: number;
  is_active: boolean;
  created_at?: string;
}

export const getOnboardingTasks = () => apiFetch<OnboardingTask[]>("/admin/onboarding-tasks");
export const createOnboardingTask = (data: Omit<OnboardingTask, "id" | "created_at">) =>
  apiFetch<OnboardingTask>("/admin/onboarding-tasks", { method: "POST", body: JSON.stringify(data) });
export const updateOnboardingTask = (id: number, data: Omit<OnboardingTask, "id" | "created_at">) =>
  apiFetch<OnboardingTask>(`/admin/onboarding-tasks/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteOnboardingTask = (id: number) =>
  apiFetch<void>(`/admin/onboarding-tasks/${id}`, { method: "DELETE" });



export interface Department {
  id: number;
  name: string;
  description?: string;
  head_name?: string;
  is_active: boolean;
}

export const getDepartments = () => apiFetch<Department[]>("/admin/departments");
export const createDepartment = (data: Omit<Department, "id">) =>
  apiFetch<Department>("/admin/departments", { method: "POST", body: JSON.stringify(data) });
export const updateDepartment = (id: number, data: Omit<Department, "id">) =>
  apiFetch<Department>(`/admin/departments/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteDepartment = (id: number) =>
  apiFetch<void>(`/admin/departments/${id}`, { method: "DELETE" });



export interface LogEntry {
  id: number;
  employee_name?: string;
  message?: string;
  reply?: string;
  locale?: string;
  mood?: string;
  created_at?: string;
}

export const getLogs = () => apiFetch<LogEntry[]>("/admin/logs");

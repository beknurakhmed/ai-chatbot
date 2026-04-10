const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface HistoryMsg {
  role: string;
  content: string;
}

export async function sendMessage(
  message: string,
  locale: string,
  history: HistoryMsg[] = [],
  employeeName?: string | null,
): Promise<{
  reply: string;
  mood: string;
  onboarding?: Array<{ id: number; title: string; description: string | null; category: string }>;
}> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      locale,
      history,
      employee_name: employeeName || undefined,
    }),
  });

  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export function getTtsUrl(text: string, locale: string): string {
  return `${API_BASE}/api/tts?text=${encodeURIComponent(text)}&locale=${locale}`;
}

export async function fetchOnboardingTasks(): Promise<
  Array<{ id: number; title: string; description: string | null; category: string; order_num: number }>
> {
  try {
    const res = await fetch(`${API_BASE}/api/onboarding/tasks`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchOnboardingProgress(employeeName: string): Promise<{
  employee_name: string;
  total: number;
  completed: number;
  tasks: Array<{ id: number; title: string; description: string | null; category: string; is_completed: boolean }>;
}> {
  const res = await fetch(`${API_BASE}/api/onboarding/progress/${encodeURIComponent(employeeName)}`);
  if (!res.ok) throw new Error("Failed to fetch progress");
  return res.json();
}

export async function completeOnboardingTask(employeeName: string, taskId: number): Promise<void> {
  await fetch(`${API_BASE}/api/onboarding/complete?employee_name=${encodeURIComponent(employeeName)}&task_id=${taskId}`, {
    method: "POST",
  });
}

export async function uncompleteOnboardingTask(employeeName: string, taskId: number): Promise<void> {
  await fetch(`${API_BASE}/api/onboarding/uncomplete?employee_name=${encodeURIComponent(employeeName)}&task_id=${taskId}`, {
    method: "POST",
  });
}

export async function submitSurvey(data: {
  employee_name: string;
  mood_score: number;
  comment?: string;
  category?: string;
  survey_date: string;
}): Promise<void> {
  await fetch(`${API_BASE}/api/survey`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

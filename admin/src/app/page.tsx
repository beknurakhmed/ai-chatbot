"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import PageHeader from "@/components/PageHeader";

interface AdminStats {
  counts: {
    knowledge: number;
    keywords: number;
    onboarding_tasks: number;
    departments: number;
    employee_progress: number;
    surveys: number;
    logs: number;
  };
  llm_mode: string;
  avg_mood: number | null;
}

const statCards: {
  key: keyof AdminStats["counts"];
  label: string;
  gradient: string;
  icon: string;
}[] = [
  { key: "knowledge", label: "Knowledge Entries", gradient: "from-blue-500 to-blue-600", icon: "\uD83D\uDCD6" },
  { key: "keywords", label: "Keywords", gradient: "from-green-500 to-green-600", icon: "\uD83D\uDD11" },
  { key: "onboarding_tasks", label: "Onboarding Tasks", gradient: "from-purple-500 to-purple-600", icon: "\uD83D\uDCCB" },
  { key: "departments", label: "Departments", gradient: "from-orange-500 to-orange-600", icon: "\uD83C\uDFE2" },
  { key: "employee_progress", label: "Employee Progress", gradient: "from-teal-500 to-teal-600", icon: "\uD83D\uDCCA" },
  { key: "surveys", label: "Pulse Surveys", gradient: "from-rose-500 to-rose-600", icon: "\uD83D\uDE0A" },
  { key: "logs", label: "Chat Logs", gradient: "from-amber-500 to-amber-600", icon: "\uD83D\uDCAC" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadStats() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<AdminStats>("/admin/stats");
      setStats(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load stats");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div>
      <PageHeader
        title="Uzum HR Dashboard"
        description={stats?.llm_mode ? `LLM Mode: ${stats.llm_mode}` : "Onboarding & Well-being Admin"}
      />

      {loading && (
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <svg className="animate-spin w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading stats...
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mb-6">
          {error}
          <button onClick={loadStats} className="ml-3 underline text-sm">Retry</button>
        </div>
      )}

      {!loading && !error && stats && (
        <>
          {/* Avg mood card */}
          {stats.avg_mood !== null && (
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl p-6 mb-6 shadow-lg">
              <div className="flex items-center gap-4">
                <span className="text-4xl">
                  {stats.avg_mood >= 4 ? "\uD83D\uDE0A" : stats.avg_mood >= 3 ? "\uD83D\uDE10" : "\uD83D\uDE1F"}
                </span>
                <div>
                  <p className="text-sm opacity-80">Average Employee Mood</p>
                  <p className="text-3xl font-bold">{stats.avg_mood} / 5</p>
                </div>
              </div>
            </div>
          )}

          {/* Stat cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {statCards.map((card) => (
              <div
                key={card.key}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 flex items-center gap-4 hover:shadow-md transition-shadow"
              >
                <div
                  className={`bg-gradient-to-br ${card.gradient} w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl shrink-0`}
                >
                  {card.icon}
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                    {stats.counts[card.key]}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

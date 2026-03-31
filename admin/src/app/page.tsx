"use client";

import { useEffect, useState } from "react";
import { apiFetch, refreshNews, refreshStaff, refreshTimetable } from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { toast } from "sonner";

interface AdminStats {
  counts: {
    knowledge: number;
    keywords: number;
    news: number;
    staff: number;
    timetable: number;
    buildings: number;
    rooms: number;
    logs: number;
  };
  llm_mode: string;
}

const statCards: {
  key: keyof AdminStats["counts"];
  label: string;
  gradient: string;
  icon: string;
}[] = [
  { key: "knowledge", label: "Knowledge Entries", gradient: "from-blue-500 to-blue-600", icon: "\uD83D\uDCD6" },
  { key: "keywords", label: "Keywords", gradient: "from-green-500 to-green-600", icon: "\uD83D\uDD11" },
  { key: "news", label: "News Items", gradient: "from-purple-500 to-purple-600", icon: "\uD83D\uDCF0" },
  { key: "staff", label: "Staff Members", gradient: "from-orange-500 to-orange-600", icon: "\uD83D\uDC65" },
  { key: "timetable", label: "Timetable Entries", gradient: "from-teal-500 to-teal-600", icon: "\uD83D\uDCC5" },
  { key: "buildings", label: "Buildings", gradient: "from-rose-500 to-rose-600", icon: "\uD83C\uDFE2" },
  { key: "rooms", label: "Rooms", gradient: "from-indigo-500 to-indigo-600", icon: "\uD83D\uDEAA" },
  { key: "logs", label: "Recent Logs", gradient: "from-amber-500 to-amber-600", icon: "\uD83D\uDCCB" },
];

export default function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<string | null>(null);

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

  async function handleRefresh(type: "news" | "staff" | "timetable") {
    setRefreshing(type);
    try {
      if (type === "news") {
        const res = await refreshNews();
        toast.success(`News refreshed: ${res.added} added, ${res.fetched} fetched`);
      } else if (type === "staff") {
        const res = await refreshStaff();
        toast.success(`Staff refreshed: ${res.count} members`);
      } else if (type === "timetable") {
        const res = await refreshTimetable();
        toast.success(`Timetable refreshed: ${res.classes} classes, ${res.entries_saved} entries`);
      }
      await loadStats();
    } catch (e) {
      toast.error(`Failed to refresh ${type}: ${e instanceof Error ? e.message : "Unknown error"}`);
    } finally {
      setRefreshing(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description={stats?.llm_mode ? `LLM Mode: ${stats.llm_mode}` : "Admin overview"}
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
          <button onClick={loadStats} className="ml-3 underline text-sm">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && stats && (
        <>
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

          {/* Quick Actions */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick Actions</h2>
            <div className="flex flex-wrap gap-3">
              {(["news", "staff", "timetable"] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => handleRefresh(type)}
                  disabled={refreshing !== null}
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${
                      refreshing === type
                        ? "bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-wait"
                        : "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 border border-blue-200 dark:border-blue-800"
                    }`}
                >
                  {refreshing === type && (
                    <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                  )}
                  Refresh {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

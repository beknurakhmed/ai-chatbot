"use client";

import { useEffect, useState } from "react";
import { getKnowledge, getKeywords, getNews, getLogs } from "@/lib/api";

interface DashboardCounts {
  knowledge: number;
  keywords: number;
  news: number;
  logs: number;
}

export default function DashboardPage() {
  const [counts, setCounts] = useState<DashboardCounts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [knowledge, keywords, news, logs] = await Promise.all([
          getKnowledge(),
          getKeywords(),
          getNews(),
          getLogs(),
        ]);
        setCounts({
          knowledge: knowledge.length,
          keywords: keywords.length,
          news: news.length,
          logs: logs.length,
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const cards = counts
    ? [
        { label: "Knowledge Entries", value: counts.knowledge, color: "bg-blue-500" },
        { label: "Keywords", value: counts.keywords, color: "bg-green-500" },
        { label: "News Items", value: counts.news, color: "bg-purple-500" },
        { label: "Recent Logs", value: counts.logs, color: "bg-orange-500" },
      ]
    : [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 text-gray-800">Dashboard</h1>

      {loading && (
        <p className="text-gray-500">Loading...</p>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-2 gap-6 max-w-2xl">
          {cards.map((card) => (
            <div
              key={card.label}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex items-center gap-4"
            >
              <div
                className={`${card.color} w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl font-bold`}
              >
                {card.value}
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold text-gray-800">{card.value}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

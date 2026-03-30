"use client";

import { useEffect, useState } from "react";
import {
  NewsItem,
  getNews,
  createNews,
  updateNews,
  deleteNews,
  refreshNews,
} from "@/lib/api";

const emptyForm = (): Omit<NewsItem, "id"> => ({
  title: "",
  published_at: "",
  is_active: true,
  url: "",
});

export default function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const [refreshing, setRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setItems(await getNews());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function openAdd() {
    setEditId(null);
    setForm(emptyForm());
    setShowForm(true);
  }

  function openEdit(item: NewsItem) {
    setEditId(item.id);
    setForm({
      title: item.title,
      published_at: item.published_at,
      is_active: item.is_active,
      url: item.url,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId !== null) {
        await updateNews(editId, form);
      } else {
        await createNews(form);
      }
      setShowForm(false);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteNews(id);
      setDeleteId(null);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshResult(null);
    try {
      const result = await refreshNews();
      setRefreshResult(`Added ${result.added} new article(s) from ajou.uz`);
      await load();
    } catch (e) {
      setRefreshResult(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  function formatDate(dateStr: string) {
    if (!dateStr) return "-";
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">News</h1>
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {refreshing ? "Refreshing..." : "Refresh from ajou.uz"}
          </button>
          <button
            onClick={openAdd}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + Add News
          </button>
        </div>
      </div>

      {refreshResult && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4 flex items-center justify-between">
          <span>{refreshResult}</span>
          <button onClick={() => setRefreshResult(null)} className="text-green-500 hover:text-green-700 text-lg leading-none">
            &times;
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Title</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Published</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Active</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">URL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{item.id}</td>
                  <td className="px-4 py-3 font-medium max-w-xs truncate">{item.title}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(item.published_at)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        item.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {item.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 text-xs truncate block max-w-xs"
                      >
                        Link
                      </a>
                    ) : (
                      <span className="text-gray-400 text-xs">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      onClick={() => openEdit(item)}
                      className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteId(item.id)}
                      className="text-red-600 hover:text-red-800 text-xs font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    No news items found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800">
                {editId !== null ? "Edit News" : "Add News"}
              </h2>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Published At</label>
                <input
                  type="text"
                  value={form.published_at}
                  onChange={(e) => setForm({ ...form, published_at: e.target.value })}
                  placeholder="e.g. 2024-01-15T10:00:00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
                <input
                  type="text"
                  value={form.url}
                  onChange={(e) => setForm({ ...form, url: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active_news"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="w-4 h-4 accent-blue-600"
                />
                <label htmlFor="is_active_news" className="text-sm font-medium text-gray-700">
                  Active
                </label>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {deleteId !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Confirm Delete</h2>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete news item #{deleteId}?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteId(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteId)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

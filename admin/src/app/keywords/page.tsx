"use client";

import { useEffect, useState } from "react";
import {
  Keyword,
  getKeywords,
  createKeyword,
  updateKeyword,
  deleteKeyword,
} from "@/lib/api";

const INTENTS = ["timetable", "staff", "admission", "news", "map", "contacts", "general"];
const LANGUAGES = ["en", "ru", "uz", "kr", "all"];

const emptyForm = (): Omit<Keyword, "id"> => ({
  keyword: "",
  intent: "general",
  language: "all",
  is_active: true,
});

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setKeywords(await getKeywords());
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

  function openEdit(kw: Keyword) {
    setEditId(kw.id);
    setForm({
      keyword: kw.keyword,
      intent: kw.intent,
      language: kw.language,
      is_active: kw.is_active,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId !== null) {
        await updateKeyword(editId, form);
      } else {
        await createKeyword(form);
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
      await deleteKeyword(id);
      setDeleteId(null);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Keywords</h1>
        <button
          onClick={openAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + Add Keyword
        </button>
      </div>

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
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Keyword</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Intent</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Language</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Active</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {keywords.map((kw) => (
                <tr key={kw.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{kw.id}</td>
                  <td className="px-4 py-3 font-medium">{kw.keyword}</td>
                  <td className="px-4 py-3">
                    <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-medium">
                      {kw.intent}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">
                      {kw.language}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        kw.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {kw.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      onClick={() => openEdit(kw)}
                      className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteId(kw.id)}
                      className="text-red-600 hover:text-red-800 text-xs font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {keywords.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    No keywords found
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
                {editId !== null ? "Edit Keyword" : "Add Keyword"}
              </h2>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Keyword</label>
                <input
                  type="text"
                  value={form.keyword}
                  onChange={(e) => setForm({ ...form, keyword: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Intent</label>
                <select
                  value={form.intent}
                  onChange={(e) => setForm({ ...form, intent: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {INTENTS.map((i) => (
                    <option key={i} value={i}>{i}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
                <select
                  value={form.language}
                  onChange={(e) => setForm({ ...form, language: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active_kw"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="w-4 h-4 accent-blue-600"
                />
                <label htmlFor="is_active_kw" className="text-sm font-medium text-gray-700">
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
              Are you sure you want to delete keyword #{deleteId}?
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

"use client";

import { useEffect, useState } from "react";
import {
  StaffMember,
  getStaff,
  createStaff,
  updateStaff,
  deleteStaff,
  refreshStaff,
} from "@/lib/api";

const CATEGORIES = ["leadership", "deans", "staff", "lecturers"];

const emptyForm = (): Omit<StaffMember, "id"> => ({
  name: "",
  position: "",
  photo: "",
  category: "staff",
  is_active: true,
});

export default function StaffPage() {
  const [staffList, setStaffList] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setStaffList(await getStaff());
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

  function openEdit(member: StaffMember) {
    setEditId(member.id);
    setForm({
      name: member.name,
      position: member.position || "",
      photo: member.photo || "",
      category: member.category || "staff",
      is_active: member.is_active,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId !== null) {
        await updateStaff(editId, form);
      } else {
        await createStaff(form);
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
      await deleteStaff(id);
      setDeleteId(null);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const data = await refreshStaff();
      setRefreshMsg(`Refreshed successfully. ${data.count} staff member(s) loaded.`);
      await load();
    } catch (e) {
      setRefreshMsg(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Staff</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {refreshing ? "Refreshing..." : "Refresh from ajou.uz"}
          </button>
          <button
            onClick={openAdd}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Staff Member
          </button>
        </div>
      </div>

      {refreshMsg && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4 text-sm">
          {refreshMsg}
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Position</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Category</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Active</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {staffList.map((member) => (
                <tr key={member.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{member.id}</td>
                  <td className="px-4 py-3 font-medium">{member.name}</td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">{member.position || "—"}</td>
                  <td className="px-4 py-3">
                    {member.category ? (
                      <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs font-medium">
                        {member.category}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        member.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {member.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      onClick={() => openEdit(member)}
                      className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeleteId(member.id)}
                      className="text-red-600 hover:text-red-800 text-xs font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {staffList.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                    No staff members found
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
                {editId !== null ? "Edit Staff Member" : "Add Staff Member"}
              </h2>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                <input
                  type="text"
                  value={form.position || ""}
                  onChange={(e) => setForm({ ...form, position: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Photo URL</label>
                <input
                  type="text"
                  value={form.photo || ""}
                  onChange={(e) => setForm({ ...form, photo: e.target.value })}
                  placeholder="https://..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={form.category || "staff"}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active_staff"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="w-4 h-4 accent-blue-600"
                />
                <label htmlFor="is_active_staff" className="text-sm font-medium text-gray-700">
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
              Are you sure you want to delete staff member #{deleteId}?
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

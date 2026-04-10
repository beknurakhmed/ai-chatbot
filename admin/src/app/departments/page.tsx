"use client";

import { useEffect, useState } from "react";
import {
  Department,
  getDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment,
} from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { toast } from "sonner";

const emptyForm = (): Omit<Department, "id"> => ({
  name: "",
  description: "",
  head_name: "",
  is_active: true,
});

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setDepartments(await getDepartments());
    } catch {
      toast.error("Failed to load departments");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function openNew() {
    setEditId(null);
    setForm(emptyForm());
    setShowForm(true);
  }

  function openEdit(dept: Department) {
    setEditId(dept.id);
    setForm({
      name: dept.name,
      description: dept.description || "",
      head_name: dept.head_name || "",
      is_active: dept.is_active,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId) {
        await updateDepartment(editId, form);
        toast.success("Department updated");
      } else {
        await createDepartment(form);
        toast.success("Department created");
      }
      setShowForm(false);
      await load();
    } catch {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this department?")) return;
    try {
      await deleteDepartment(id);
      toast.success("Department deleted");
      await load();
    } catch {
      toast.error("Delete failed");
    }
  }

  return (
    <div>
      <PageHeader title="Departments" description="Manage company departments and teams" />

      <button
        onClick={openNew}
        className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
      >
        + Add Department
      </button>

      {showForm && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Head Name</label>
              <input
                value={form.head_name || ""}
                onChange={(e) => setForm({ ...form, head_name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={form.description || ""}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              Active
            </label>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleSave}
              disabled={saving || !form.name}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm"
            >
              {saving ? "Saving..." : editId ? "Update" : "Create"}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-lg text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700">
          {departments.map((dept) => (
            <div key={dept.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <span className="font-medium">{dept.name}</span>
                {dept.description && (
                  <p className="text-sm text-gray-500">{dept.description}</p>
                )}
                {dept.head_name && (
                  <p className="text-xs text-gray-400">Head: {dept.head_name}</p>
                )}
              </div>
              <div className="flex gap-2 shrink-0">
                <button onClick={() => openEdit(dept)} className="text-sm text-blue-600 hover:underline">
                  Edit
                </button>
                <button onClick={() => handleDelete(dept.id)} className="text-sm text-red-500 hover:underline">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import {
  OnboardingTask,
  getOnboardingTasks,
  createOnboardingTask,
  updateOnboardingTask,
  deleteOnboardingTask,
} from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { toast } from "sonner";

const CATEGORIES = ["day_1", "week_1", "week_2", "month_1"];

const emptyForm = (): Omit<OnboardingTask, "id" | "created_at"> => ({
  title: "",
  description: "",
  category: "day_1",
  order_num: 0,
  is_active: true,
});

export default function OnboardingPage() {
  const [tasks, setTasks] = useState<OnboardingTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setTasks(await getOnboardingTasks());
    } catch (e) {
      toast.error("Failed to load tasks");
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

  function openEdit(task: OnboardingTask) {
    setEditId(task.id);
    setForm({
      title: task.title,
      description: task.description || "",
      category: task.category,
      order_num: task.order_num,
      is_active: task.is_active,
    });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId) {
        await updateOnboardingTask(editId, form);
        toast.success("Task updated");
      } else {
        await createOnboardingTask(form);
        toast.success("Task created");
      }
      setShowForm(false);
      await load();
    } catch (e) {
      toast.error("Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this task?")) return;
    try {
      await deleteOnboardingTask(id);
      toast.success("Task deleted");
      await load();
    } catch (e) {
      toast.error("Delete failed");
    }
  }

  const grouped = CATEGORIES.map((cat) => ({
    category: cat,
    tasks: tasks.filter((t) => t.category === cat),
  }));

  return (
    <div>
      <PageHeader title="Onboarding Tasks" description="Manage the onboarding checklist for new employees" />

      <button
        onClick={openNew}
        className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
      >
        + Add Task
      </button>

      {showForm && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Title</label>
              <input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
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
            <div>
              <label className="block text-sm font-medium mb-1">Order</label>
              <input
                type="number"
                value={form.order_num}
                onChange={(e) => setForm({ ...form, order_num: parseInt(e.target.value) || 0 })}
                className="w-full border rounded-lg px-3 py-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            <div className="flex items-end gap-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                Active
              </label>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleSave}
              disabled={saving || !form.title}
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
        <div className="space-y-6">
          {grouped.map(({ category, tasks: catTasks }) => (
            <div key={category}>
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2 capitalize">
                {category.replace("_", " ")}
              </h3>
              {catTasks.length === 0 ? (
                <p className="text-gray-400 text-sm">No tasks in this category</p>
              ) : (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700">
                  {catTasks.map((task) => (
                    <div key={task.id} className="flex items-center justify-between px-4 py-3">
                      <div>
                        <span className={`font-medium ${task.is_active ? "" : "line-through text-gray-400"}`}>
                          {task.title}
                        </span>
                        {task.description && (
                          <p className="text-sm text-gray-500 mt-0.5">{task.description}</p>
                        )}
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={() => openEdit(task)}
                          className="text-sm text-blue-600 hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(task.id)}
                          className="text-sm text-red-500 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

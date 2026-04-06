"use client";

import { useEffect, useState } from "react";
import {
  BuildingEntry,
  getBuildings,
  createBuilding,
  updateBuilding,
  deleteBuilding,
} from "@/lib/api";

const COLORS = [
  "bg-gray-500", "bg-blue-500", "bg-emerald-500", "bg-orange-500",
  "bg-purple-500", "bg-pink-500", "bg-red-500", "bg-yellow-500", "bg-teal-500",
];

const emptyForm = (): Omit<BuildingEntry, "id"> => ({
  num: 1,
  name: "",
  description: "",
  color: "bg-blue-500",
  is_active: true,
});

export default function BuildingsPage() {
  const [buildings, setBuildings] = useState<BuildingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  // Campus map image URL (stored as building num=0)
  const [mapUrl, setMapUrl] = useState("");
  const [mapId, setMapId] = useState<number | null>(null);
  const [savingMap, setSavingMap] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const all = await getBuildings();
      const mapEntry = all.find((b) => b.num === 0);
      if (mapEntry) {
        setMapUrl(mapEntry.photo || "");
        setMapId(mapEntry.id);
      }
      setBuildings(all.filter((b) => b.num > 0));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function saveMapUrl() {
    setSavingMap(true);
    try {
      if (mapId !== null) {
        await updateBuilding(mapId, { num: 0, name: "Campus Map", description: "Map image URL", photo: mapUrl, color: "bg-blue-500", is_active: true });
      } else {
        await createBuilding({ num: 0, name: "Campus Map", description: "Map image URL", photo: mapUrl, color: "bg-blue-500", is_active: true });
      }
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingMap(false);
    }
  }

  function openAdd() {
    setEditId(null);
    setForm(emptyForm());
    setShowForm(true);
  }

  function openEdit(b: BuildingEntry) {
    setEditId(b.id);
    setForm({ num: b.num, name: b.name, description: b.description || "", color: b.color, is_active: b.is_active });
    setShowForm(true);
  }

  async function handleSave() {
    setSaving(true);
    try {
      if (editId !== null) {
        await updateBuilding(editId, form);
      } else {
        await createBuilding(form);
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
      await deleteBuilding(id);
      setDeleteId(null);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">Buildings</h1>
        <button onClick={openAdd} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
          + Add Building
        </button>
      </div>

      {/* Campus Map Image URL */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Campus Map Image</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={mapUrl}
            onChange={(e) => setMapUrl(e.target.value)}
            placeholder="https://example.com/campus-map.jpg or /campus/map.jpg"
            className="flex-1 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={saveMapUrl}
            disabled={savingMap}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {savingMap ? "..." : "Save"}
          </button>
        </div>
        {mapUrl && (
          <img src={mapUrl} alt="Campus Map Preview" className="mt-3 w-full max-h-48 object-contain rounded-lg border border-gray-200 dark:border-gray-600" />
        )}
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 dark:bg-red-900/30 dark:border-red-800 dark:text-red-400 px-4 py-3 rounded mb-4">{error}</div>}

      {loading ? (
        <p className="text-gray-500 dark:text-gray-400">Loading...</p>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Num</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Color</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Description</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Active</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {buildings.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-4 py-3 font-bold">{b.num}</td>
                  <td className="px-4 py-3">
                    <span className={`${b.color} text-white w-6 h-6 rounded inline-flex items-center justify-center text-xs font-bold`}>
                      {b.num}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium">{b.name}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{b.description || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${b.is_active ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" : "bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400"}`}>
                      {b.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button onClick={() => openEdit(b)} className="text-blue-600 hover:text-blue-800 text-xs font-medium">Edit</button>
                    <button onClick={() => setDeleteId(b.id)} className="text-red-600 hover:text-red-800 text-xs font-medium">Delete</button>
                  </td>
                </tr>
              ))}
              {buildings.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400 dark:text-gray-500">No buildings found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">{editId !== null ? "Edit Building" : "Add Building"}</h2>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Number</label>
                <input type="number" value={form.num} onChange={(e) => setForm({ ...form, num: parseInt(e.target.value) || 1 })}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <input type="text" value={form.description || ""} onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Color</label>
                <div className="flex flex-wrap gap-2">
                  {COLORS.map((c) => (
                    <button key={c} onClick={() => setForm({ ...form, color: c })}
                      className={`${c} w-8 h-8 rounded-lg ${form.color === c ? "ring-2 ring-offset-2 ring-blue-500" : ""}`} />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="is_active_bld" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  className="w-4 h-4 accent-blue-600" />
                <label htmlFor="is_active_bld" className="text-sm font-medium text-gray-700 dark:text-gray-300">Active</label>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg">Cancel</button>
              <button onClick={handleSave} disabled={saving} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50">
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteId !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">Confirm Delete</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">Are you sure you want to delete building #{deleteId}?</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteId(null)} className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg">Cancel</button>
              <button onClick={() => handleDelete(deleteId)} className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

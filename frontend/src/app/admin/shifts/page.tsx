"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";

interface Shift {
  id: number;
  department_id: number;
  start_time: string;
  end_time: string;
  total_slots: number;
  occupied_slots: number;
  status: string;
}

interface Department {
  id: number;
  name: string;
}

export default function AdminShiftsPage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    department_id: 0,
    start_time: "",
    end_time: "",
    total_slots: 1,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [s, d] = await Promise.all([
        apiFetch("/api/v1/shifts/"),
        apiFetch("/api/v1/departments/"),
      ]);
      setShifts(s);
      setDepartments(d);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch("/api/v1/shifts/", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setShowCreate(false);
      setForm({ department_id: 0, start_time: "", end_time: "", total_slots: 1 });
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handlePublish = async (id: number) => {
    try {
      await apiFetch(`/api/v1/shifts/${id}/publish`, { method: "PATCH" });
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm("Отменить смену?")) return;
    try {
      await apiFetch(`/api/v1/shifts/${id}/cancel`, { method: "PATCH" });
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Удалить смену?")) return;
    try {
      await apiFetch(`/api/v1/shifts/${id}`, { method: "DELETE" });
      loadData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: "bg-gray-100 text-gray-800",
      published: "bg-green-100 text-green-800",
      closed: "bg-blue-100 text-blue-800",
      cancelled: "bg-red-100 text-red-800",
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || ""}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Управление сменами</h1>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            + Создать смену
          </button>
        </div>

        {showCreate && (
          <form
            onSubmit={handleCreate}
            className="mb-6 p-4 bg-gray-50 border rounded-lg grid grid-cols-2 gap-4"
          >
            <select
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: Number(e.target.value) })}
              className="px-3 py-2 border rounded-lg"
              required
            >
              <option value={0}>Выберите отделение</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              min={1}
              value={form.total_slots}
              onChange={(e) => setForm({ ...form, total_slots: Number(e.target.value) })}
              className="px-3 py-2 border rounded-lg"
              placeholder="Кол-во слотов"
              required
            />
            <input
              type="datetime-local"
              value={form.start_time}
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              className="px-3 py-2 border rounded-lg"
              required
            />
            <input
              type="datetime-local"
              value={form.end_time}
              onChange={(e) => setForm({ ...form, end_time: e.target.value })}
              className="px-3 py-2 border rounded-lg"
              required
            />
            <div className="col-span-2 flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Создать
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-gray-300 rounded-lg hover:bg-gray-400"
              >
                Отмена
              </button>
            </div>
          </form>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-3">ID</th>
                  <th className="text-left p-3">Отделение</th>
                  <th className="text-left p-3">Начало</th>
                  <th className="text-left p-3">Конец</th>
                  <th className="text-left p-3">Слоты</th>
                  <th className="text-left p-3">Статус</th>
                  <th className="text-left p-3">Действия</th>
                </tr>
              </thead>
              <tbody>
                {shifts.map((shift) => (
                  <tr key={shift.id} className="border-t hover:bg-gray-50">
                    <td className="p-3">{shift.id}</td>
                    <td className="p-3">#{shift.department_id}</td>
                    <td className="p-3">
                      {new Date(shift.start_time).toLocaleString("ru-RU")}
                    </td>
                    <td className="p-3">
                      {new Date(shift.end_time).toLocaleString("ru-RU")}
                    </td>
                    <td className="p-3">
                      {shift.occupied_slots}/{shift.total_slots}
                    </td>
                    <td className="p-3">{statusBadge(shift.status)}</td>
                    <td className="p-3">
                      <div className="flex gap-1">
                        {shift.status === "draft" && (
                          <button
                            onClick={() => handlePublish(shift.id)}
                            className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                          >
                            Опубл.
                          </button>
                        )}
                        {shift.status !== "cancelled" && (
                          <button
                            onClick={() => handleCancel(shift.id)}
                            className="px-2 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700"
                          >
                            Отменить
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(shift.id)}
                          className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                        >
                          Удалить
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

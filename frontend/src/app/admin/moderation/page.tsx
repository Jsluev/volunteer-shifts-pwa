"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";

interface Registration {
  id: number;
  shift_id: number;
  user_id: number;
  user_name: string | null;
  user_email: string | null;
  status: string;
  moderator_comment: string | null;
  created_at: string | null;
}

interface Shift {
  id: number;
  department_id: number;
  start_time: string;
  end_time: string;
  total_slots: number;
  occupied_slots: number;
  status: string;
}

const statusLabels: Record<string, string> = {
  pending: "Ожидает",
  approved: "Подтверждено",
  rejected: "Отклонено",
  cancelled: "Отменено",
  attendance_confirmed: "Подтв. присутствие",
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
  attendance_confirmed: "bg-blue-100 text-blue-800",
};

export default function ModerationPage() {
  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [selectedShift, setSelectedShift] = useState<number | null>(null);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState("");
  const [selected, setSelected] = useState<number[]>([]);

  useEffect(() => {
    loadShifts();
  }, []);

  useEffect(() => {
    if (selectedShift) loadRegistrations();
  }, [selectedShift, filter]);

  const loadShifts = async () => {
    try {
      const data = await apiFetch("/api/v1/shifts/?status=published");
      setShifts(data);
      if (data.length > 0) setSelectedShift(data[0].id);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRegistrations = async () => {
    try {
      const params = new URLSearchParams();
      if (filter !== "all") params.set("status", filter);
      const data = await apiFetch(`/api/v1/shifts/${selectedShift}/registrations?${params}`);
      setRegistrations(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleModerate = async (regId: number, approve: boolean) => {
    try {
      await apiFetch(`/api/v1/registrations/${regId}/moderate`, {
        method: "PATCH",
        body: JSON.stringify({
          status: approve ? "approved" : "rejected",
          moderator_comment: approve ? null : comment || "Отклонено координатором",
        }),
      });
      setComment("");
      loadRegistrations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleBulk = async (approve: boolean) => {
    if (selected.length === 0) return;
    try {
      await apiFetch("/api/v1/registrations/bulk-moderate", {
        method: "POST",
        body: JSON.stringify({ registration_ids: selected, approve }),
      });
      setSelected([]);
      loadRegistrations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selected.length === registrations.length) {
      setSelected([]);
    } else {
      setSelected(registrations.map((r) => r.id));
    }
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Модерация записей</h1>

        <div className="flex gap-4 mb-6">
          <select
            value={selectedShift || ""}
            onChange={(e) => setSelectedShift(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg"
          >
            {shifts.map((s) => (
              <option key={s.id} value={s.id}>
                Смена #{s.id} — {new Date(s.start_time).toLocaleDateString("ru-RU")} ({s.occupied_slots}/{s.total_slots})
              </option>
            ))}
          </select>

          <div className="flex gap-1">
            {["pending", "approved", "rejected", "all"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-2 rounded-lg text-sm ${
                  filter === f ? "bg-blue-600 text-white" : "bg-gray-100 hover:bg-gray-200"
                }`}
              >
                {f === "all" ? "Все" : statusLabels[f]}
              </button>
            ))}
          </div>
        </div>

        {selected.length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-4">
            <span className="text-sm">Выбрано: {selected.length}</span>
            <button
              onClick={() => handleBulk(true)}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
            >
              Одобрить все
            </button>
            <button
              onClick={() => handleBulk(false)}
              className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
            >
              Отклонить все
            </button>
            <button
              onClick={() => setSelected([])}
              className="px-3 py-1 bg-gray-300 text-sm rounded hover:bg-gray-400"
            >
              Снять выделение
            </button>
          </div>
        )}

        {filter === "rejected" && (
          <div className="mb-4">
            <input
              type="text"
              placeholder="Причина отказа (если нужна)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="px-4 py-2 border rounded-lg w-96"
            />
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : registrations.length === 0 ? (
          <div className="text-center py-12 text-gray-500">Нет заявок</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="p-3 w-10">
                    <input
                      type="checkbox"
                      checked={selected.length === registrations.length && registrations.length > 0}
                      onChange={toggleAll}
                    />
                  </th>
                  <th className="text-left p-3">Волонтёр</th>
                  <th className="text-left p-3">Email</th>
                  <th className="text-left p-3">Статус</th>
                  <th className="text-left p-3">Дата заявки</th>
                  <th className="text-left p-3">Комментарий</th>
                  <th className="text-left p-3">Действия</th>
                </tr>
              </thead>
              <tbody>
                {registrations.map((reg) => (
                  <tr key={reg.id} className="border-t hover:bg-gray-50">
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selected.includes(reg.id)}
                        onChange={() => toggleSelect(reg.id)}
                      />
                    </td>
                    <td className="p-3 font-medium">{reg.user_name || `#${reg.user_id}`}</td>
                    <td className="p-3 text-gray-500">{reg.user_email}</td>
                    <td className="p-3">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[reg.status]}`}>
                        {statusLabels[reg.status]}
                      </span>
                    </td>
                    <td className="p-3 text-gray-500">
                      {reg.created_at ? new Date(reg.created_at).toLocaleString("ru-RU") : "—"}
                    </td>
                    <td className="p-3 text-gray-500 text-xs">{reg.moderator_comment || "—"}</td>
                    <td className="p-3">
                      {reg.status === "pending" && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleModerate(reg.id, true)}
                            className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                          >
                            Одобрить
                          </button>
                          <button
                            onClick={() => handleModerate(reg.id, false)}
                            className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                          >
                            Отклонить
                          </button>
                        </div>
                      )}
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

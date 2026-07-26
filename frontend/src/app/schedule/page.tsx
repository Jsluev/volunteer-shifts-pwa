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

export default function SchedulePage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ department: "", date: "" });

  useEffect(() => {
    loadShifts();
  }, []);

  const loadShifts = async () => {
    try {
      const data = await apiFetch("/api/v1/shifts/?status=published");
      setShifts(data.items || data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (shiftId: number) => {
    try {
      await apiFetch("/api/v1/registrations/", {
        method: "POST",
        body: JSON.stringify({ shift_id: shiftId }),
      });
      loadShifts();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const getStatusColor = (shift: Shift) => {
    const ratio = shift.occupied_slots / shift.total_slots;
    if (ratio >= 1) return "bg-red-100 border-red-300";
    if (ratio >= 0.8) return "bg-yellow-100 border-yellow-300";
    return "bg-green-100 border-green-300";
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Расписание дежурств</h1>

        <div className="mb-6 flex gap-4">
          <input
            type="date"
            value={filter.date}
            onChange={(e) => setFilter({ ...filter, date: e.target.value })}
            className="px-4 py-2 border rounded-lg"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shifts.map((shift) => (
            <div
              key={shift.id}
              className={`p-4 rounded-lg border-2 ${getStatusColor(shift)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-medium px-2 py-1 bg-white rounded">
                  Отделение #{shift.department_id}
                </span>
                <span className="text-sm font-bold">
                  {shift.occupied_slots}/{shift.total_slots}
                </span>
              </div>
              <p className="text-sm text-gray-700 mb-1">
                {formatDate(shift.start_time)}
              </p>
              <p className="text-sm text-gray-700 mb-3">
                — {formatDate(shift.end_time)}
              </p>
              <button
                onClick={() => handleRegister(shift.id)}
                disabled={shift.occupied_slots >= shift.total_slots}
                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
              >
                {shift.occupied_slots >= shift.total_slots ? "Мест нет" : "Записаться"}
              </button>
            </div>
          ))}
        </div>

        {shifts.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            Нет доступных смен
          </div>
        )}
      </main>
    </div>
  );
}

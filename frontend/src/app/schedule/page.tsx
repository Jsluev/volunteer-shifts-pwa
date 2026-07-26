"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";
import { toast } from "@/components/Toast";

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

export default function SchedulePage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ department_id: "", start_date: "", end_date: "" });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [s, d] = await Promise.all([
        apiFetch("/api/v1/shifts/?status=published"),
        apiFetch("/api/v1/departments/"),
      ]);
      setShifts(s.items || s);
      setDepartments(d);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredShifts = shifts.filter((s) => {
    if (filter.department_id && s.department_id !== Number(filter.department_id)) return false;
    if (filter.start_date && new Date(s.start_time) < new Date(filter.start_date)) return false;
    if (filter.end_date && new Date(s.end_time) > new Date(filter.end_date + "T23:59:59")) return false;
    return true;
  });

  const handleRegister = async (shiftId: number) => {
    try {
      await apiFetch("/api/v1/registrations/", {
        method: "POST",
        body: JSON.stringify({ shift_id: shiftId }),
      });
      toast.success("Вы записаны на смену!");
      loadData();
    } catch (err: any) {
      toast.error(err.message);
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

  const getDeptName = (id: number) => {
    const dept = departments.find((d) => d.id === id);
    return dept ? dept.name : `#${id}`;
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

        <div className="mb-6 flex flex-wrap gap-4">
          <select
            value={filter.department_id}
            onChange={(e) => setFilter({ ...filter, department_id: e.target.value })}
            className="px-4 py-2 border rounded-lg text-sm"
          >
            <option value="">Все отделения</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          <input
            type="date"
            value={filter.start_date}
            onChange={(e) => setFilter({ ...filter, start_date: e.target.value })}
            className="px-4 py-2 border rounded-lg text-sm"
            placeholder="С даты"
          />
          <input
            type="date"
            value={filter.end_date}
            onChange={(e) => setFilter({ ...filter, end_date: e.target.value })}
            className="px-4 py-2 border rounded-lg text-sm"
            placeholder="По дату"
          />
          {(filter.department_id || filter.start_date || filter.end_date) && (
            <button
              onClick={() => setFilter({ department_id: "", start_date: "", end_date: "" })}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Сбросить
            </button>
          )}
        </div>

        <div className="mb-4 text-sm text-gray-500">
          Показано: {filteredShifts.length} из {shifts.length} смен
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredShifts.map((shift) => (
            <div
              key={shift.id}
              className={`p-4 rounded-lg border-2 ${getStatusColor(shift)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-medium px-2 py-1 bg-white rounded">
                  {getDeptName(shift.department_id)}
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

        {filteredShifts.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            {shifts.length === 0 ? "Нет доступных смен" : "Нет смен по заданным фильтрам"}
          </div>
        )}
      </main>
    </div>
  );
}

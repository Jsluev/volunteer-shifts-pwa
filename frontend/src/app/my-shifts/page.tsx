"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";

interface Registration {
  id: number;
  shift_id: number;
  status: string;
  created_at: string;
  moderator_comment: string | null;
}

const statusLabels: Record<string, string> = {
  pending: "Ожидает",
  approved: "Подтверждено",
  rejected: "Отклонено",
  cancelled: "Отменено",
  attendance_confirmed: "Присутствие подтверждено",
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
  attendance_confirmed: "bg-blue-100 text-blue-800",
};

export default function MyShiftsPage() {
  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRegistrations();
  }, []);

  const loadRegistrations = async () => {
    try {
      const data = await apiFetch("/api/v1/registrations/my");
      setRegistrations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id: number) => {
    if (!confirm("Отменить запись?")) return;
    try {
      await apiFetch(`/api/v1/registrations/${id}/cancel`, { method: "PATCH" });
      loadRegistrations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleConfirm = async (id: number) => {
    try {
      await apiFetch(`/api/v1/registrations/${id}/confirm-attendance`, {
        method: "PATCH",
      });
      loadRegistrations();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Мои смены</h1>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : registrations.length === 0 ? (
          <div className="text-center py-12 text-gray-500">У вас нет записей</div>
        ) : (
          <div className="space-y-3">
            {registrations.map((reg) => (
              <div
                key={reg.id}
                className="flex items-center justify-between p-4 bg-white border rounded-lg shadow-sm"
              >
                <div>
                  <p className="font-medium">Смена #{reg.shift_id}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(reg.created_at).toLocaleDateString("ru-RU")}
                  </p>
                  {reg.moderator_comment && (
                    <p className="text-sm text-red-600 mt-1">
                      {reg.moderator_comment}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[reg.status]}`}
                  >
                    {statusLabels[reg.status]}
                  </span>
                  {reg.status === "approved" && (
                    <button
                      onClick={() => handleConfirm(reg.id)}
                      className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700"
                    >
                      Подтвердить
                    </button>
                  )}
                  {["pending", "approved"].includes(reg.status) && (
                    <button
                      onClick={() => handleCancel(reg.id)}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
                    >
                      Отменить
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

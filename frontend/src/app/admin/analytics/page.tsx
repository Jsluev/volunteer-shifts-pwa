"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import AdminGuard from "@/components/AdminGuard";
import { apiFetch } from "@/lib/api";

interface FillRate {
  total_shifts: number;
  total_slots: number;
  filled_slots: number;
  fill_rate_percent: number;
  empty_slots: number;
}

interface AuditLogEntry {
  id: number;
  user_id: number;
  action_type: string;
  meta: Record<string, unknown>;
  created_at: string | null;
}

interface VolunteerClassification {
  total_volunteers: number;
  classifications: Record<string, { count: number; volunteers: Array<{ id: number; name: string; email: string; shifts_this_month: number }> }>;
}

interface UnfilledShift {
  shift_id: number;
  department_id: number;
  start_time: string;
  end_time: string;
  total_slots: number;
  occupied: number;
  empty: number;
}

const actionLabels: Record<string, string> = {
  create_shift: "Создал смену",
  publish_shift: "Опубликовал смену",
  cancel_shift: "Отменил смену",
  delete_shift: "Удалил смену",
  change_shift: "Изменил смену",
  approve_reg: "Подтвердил запись",
  reject_reg: "Отклонил запись",
  cancel_reg: "Отменил запись",
  bulk_moderate: "Массовая модерация",
  broadcast: "Рассылка",
};

const classLabels: Record<string, string> = {
  active_3plus: "Активные (3+ смен/мес)",
  active_1_2: "Умеренные (1-2 смены/мес)",
  inactive_registered: "Зарегистрированы, не ходят",
  never_came: "Никогда не приходили",
};

export default function AnalyticsPage() {
  const [fillRate, setFillRate] = useState<FillRate | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [classification, setClassification] = useState<VolunteerClassification | null>(null);
  const [unfilled, setUnfilled] = useState<UnfilledShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "audit" | "volunteers" | "unfilled">("overview");

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [fr, al, vc, us] = await Promise.all([
        apiFetch("/api/v1/analytics/fill-rate"),
        apiFetch("/api/v1/analytics/audit?page_size=30"),
        apiFetch("/api/v1/analytics/volunteer-classification"),
        apiFetch("/api/v1/analytics/unfilled-slots"),
      ]);
      setFillRate(fr);
      setAuditLogs(al.logs || []);
      setClassification(vc);
      setUnfilled(us.shifts || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: string) => {
    alert(`Экспорт в ${format} будет доступен в следующей версии`);
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
    <AdminGuard>
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Аналитика</h1>
          <div className="flex gap-2">
            <button onClick={() => handleExport("xlsx")} className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">Excel</button>
            <button onClick={() => handleExport("csv")} className="px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">CSV</button>
            <button onClick={() => handleExport("pdf")} className="px-3 py-1 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">PDF</button>
          </div>
        </div>

        <div className="flex gap-2 mb-6">
          {(["overview", "volunteers", "unfilled", "audit"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm ${activeTab === tab ? "bg-blue-600 text-white" : "bg-gray-100 hover:bg-gray-200"}`}
            >
              {tab === "overview" && "Обзор"}
              {tab === "volunteers" && "Волонтёры"}
              {tab === "unfilled" && "Незаполненные"}
              {tab === "audit" && "Журнал"}
            </button>
          ))}
        </div>

        {activeTab === "overview" && fillRate && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <div className="p-4 bg-white border rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Смен</p>
              <p className="text-2xl font-bold">{fillRate.total_shifts}</p>
            </div>
            <div className="p-4 bg-white border rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Всего слотов</p>
              <p className="text-2xl font-bold">{fillRate.total_slots}</p>
            </div>
            <div className="p-4 bg-white border rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Занято</p>
              <p className="text-2xl font-bold text-green-600">{fillRate.filled_slots}</p>
            </div>
            <div className="p-4 bg-white border rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Свободно</p>
              <p className="text-2xl font-bold text-red-600">{fillRate.empty_slots}</p>
            </div>
            <div className="p-4 bg-white border rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">Заполняемость</p>
              <p className="text-2xl font-bold">{fillRate.fill_rate_percent}%</p>
            </div>
          </div>
        )}

        {activeTab === "volunteers" && classification && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">Всего волонтёров: {classification.total_volunteers}</p>
            {Object.entries(classLabels).map(([key, label]) => {
              const cls = classification.classifications[key];
              if (!cls) return null;
              return (
                <div key={key} className="bg-white border rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-medium">{label}</h3>
                    <span className="text-sm text-gray-500">{cls.count}</span>
                  </div>
                  {cls.volunteers.length > 0 && (
                    <div className="text-sm text-gray-600">
                      {cls.volunteers.slice(0, 5).map((v) => (
                        <span key={v.id} className="inline-block bg-gray-100 px-2 py-1 rounded mr-2 mb-1">
                          {v.name || v.email} ({v.shifts_this_month} смен)
                        </span>
                      ))}
                      {cls.volunteers.length > 5 && (
                        <span className="text-gray-400">и ещё {cls.volunteers.length - 5}...</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === "unfilled" && (
          <div>
            {unfilled.length === 0 ? (
              <div className="text-center py-12 text-gray-500">Все смены заполнены</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="text-left p-3">Смена</th>
                      <th className="text-left p-3">Отделение</th>
                      <th className="text-left p-3">Дата</th>
                      <th className="text-left p-3">Слоты</th>
                      <th className="text-left p-3">Свободно</th>
                    </tr>
                  </thead>
                  <tbody>
                    {unfilled.map((s) => (
                      <tr key={s.shift_id} className="border-t hover:bg-gray-50">
                        <td className="p-3">#{s.shift_id}</td>
                        <td className="p-3">#{s.department_id}</td>
                        <td className="p-3">{new Date(s.start_time).toLocaleString("ru-RU")}</td>
                        <td className="p-3">{s.occupied}/{s.total_slots}</td>
                        <td className="p-3 font-bold text-red-600">{s.empty}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === "audit" && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-3">Время</th>
                  <th className="text-left p-3">Пользователь</th>
                  <th className="text-left p-3">Действие</th>
                  <th className="text-left p-3">Детали</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} className="border-t hover:bg-gray-50">
                    <td className="p-3">{log.created_at ? new Date(log.created_at).toLocaleString("ru-RU") : "—"}</td>
                    <td className="p-3">#{log.user_id}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {actionLabels[log.action_type] || log.action_type}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-gray-500 max-w-xs truncate">{JSON.stringify(log.meta)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
    </AdminGuard>
  );
}

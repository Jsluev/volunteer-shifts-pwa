"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";

interface Notification {
  id: number;
  type: string;
  channel: string;
  subject: string | null;
  body: string;
  scheduled_at: string;
  sent_at: string | null;
  status: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await apiFetch("/api/v1/notifications/");
      setNotifications(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const markRead = async (id: number) => {
    try {
      await apiFetch(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
      loadNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Уведомления</h1>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-12 text-gray-500">Нет уведомлений</div>
        ) : (
          <div className="space-y-3">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                className={`p-4 border rounded-lg ${
                  notif.status === "pending"
                    ? "bg-blue-50 border-blue-200"
                    : "bg-white"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    {notif.subject && (
                      <p className="font-medium">{notif.subject}</p>
                    )}
                    <p className="text-sm text-gray-700 mt-1">{notif.body}</p>
                    <p className="text-xs text-gray-400 mt-2">
                      {new Date(notif.scheduled_at).toLocaleString("ru-RU")} •{" "}
                      {notif.channel}
                    </p>
                  </div>
                  {notif.status === "pending" && (
                    <button
                      onClick={() => markRead(notif.id)}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Прочитано
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

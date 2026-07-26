"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch, getStoredUser, clearAuth, type StoredUser } from "@/lib/api";

const navItems = [
  { href: "/schedule", label: "Расписание" },
  { href: "/my-shifts", label: "Мои смены" },
  { href: "/chat", label: "Сообщения" },
  { href: "/notifications", label: "Уведомления" },
];

const adminItems = [
  { href: "/admin/shifts", label: "Управление сменами", roles: ["coordinator", "admin"] },
  { href: "/admin/moderation", label: "Модерация", roles: ["coordinator", "admin"] },
  { href: "/admin/analytics", label: "Аналитика", roles: ["coordinator", "admin"] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [unreadCount, setUnreadCount] = useState(0);
  const [user, setUser] = useState<StoredUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  useEffect(() => {
    const loadUnread = async () => {
      try {
        const data = await apiFetch("/api/v1/notifications/unread-count");
        setUnreadCount(data.count);
      } catch {}
    };
    loadUnread();
    const interval = setInterval(loadUnread, 30000);
    return () => clearInterval(interval);
  }, []);

  const visibleAdminItems = adminItems.filter(
    (item) => user && item.roles.includes(user.role)
  );

  return (
    <aside className="w-64 bg-gray-900 text-white min-h-screen p-4 flex flex-col">
      <h2 className="text-lg font-bold mb-6 px-2">Volunteer Shifts</h2>

      {user && (
        <div className="mb-4 px-2 pb-3 border-b border-gray-700">
          <p className="text-sm font-medium truncate">{user.full_name}</p>
          <p className="text-xs text-gray-400 truncate">{user.email}</p>
          <span className="inline-block mt-1 text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
            {user.role === "coordinator" ? "Координатор" : user.role === "admin" ? "Админ" : "Волонтёр"}
          </span>
        </div>
      )}

      <nav className="space-y-1 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm ${
              pathname === item.href ? "bg-blue-600" : "hover:bg-gray-800"
            }`}
          >
            <span>{item.label}</span>
            {item.href === "/notifications" && unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                {unreadCount > 99 ? "99+" : unreadCount}
              </span>
            )}
          </Link>
        ))}
      </nav>

      {visibleAdminItems.length > 0 && (
        <div className="mt-8">
          <p className="text-xs text-gray-500 uppercase px-2 mb-2">Управление</p>
          <nav className="space-y-1">
            {visibleAdminItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`block px-3 py-2 rounded-lg text-sm ${
                  pathname === item.href ? "bg-blue-600" : "hover:bg-gray-800"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      )}

      <div className="mt-4">
        <button
          onClick={() => {
            clearAuth();
            window.location.href = "/";
          }}
          className="w-full px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg"
        >
          Выйти
        </button>
      </div>
    </aside>
  );
}

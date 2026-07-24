"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch } from "@/lib/api";

interface Dialog {
  id: number;
  type: string;
  participant_ids: number[];
}

interface Message {
  id: number;
  dialog_id: number;
  sender_id: number;
  text: string;
  created_at: string;
}

export default function ChatPage() {
  const [dialogs, setDialogs] = useState<Dialog[]>([]);
  const [selectedDialog, setSelectedDialog] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDialogs();
  }, []);

  const loadDialogs = async () => {
    try {
      const data = await apiFetch("/api/v1/chat/dialogs");
      setDialogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (dialogId: number) => {
    setSelectedDialog(dialogId);
    try {
      const data = await apiFetch(`/api/v1/chat/dialogs/${dialogId}/messages`);
      setMessages(data);
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedDialog) return;
    try {
      await apiFetch("/api/v1/chat/messages", {
        method: "POST",
        body: JSON.stringify({ dialog_id: selectedDialog, text: newMessage }),
      });
      setNewMessage("");
      loadMessages(selectedDialog);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex">
        <div className="w-64 border-r bg-gray-50 p-4">
          <h2 className="font-bold mb-4">Диалоги</h2>
          {loading ? (
            <p className="text-sm text-gray-500">Загрузка...</p>
          ) : dialogs.length === 0 ? (
            <p className="text-sm text-gray-500">Нет диалогов</p>
          ) : (
            <div className="space-y-2">
              {dialogs.map((d) => (
                <button
                  key={d.id}
                  onClick={() => loadMessages(d.id)}
                  className={`w-full text-left p-3 rounded-lg text-sm ${
                    selectedDialog === d.id
                      ? "bg-blue-100"
                      : "hover:bg-gray-200"
                  }`}
                >
                  {d.type === "group"
                    ? `Группа #${d.id}`
                    : `Диалог #${d.id}`}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col">
          {selectedDialog ? (
            <>
              <div className="flex-1 overflow-auto p-4 space-y-3">
                {messages.map((msg) => (
                  <div key={msg.id} className="max-w-md">
                    <div className="bg-gray-100 rounded-lg px-4 py-2">
                      <p className="text-sm">{msg.text}</p>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(msg.created_at).toLocaleTimeString("ru-RU")}
                    </p>
                  </div>
                ))}
              </div>
              <div className="border-t p-4 flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  placeholder="Сообщение..."
                  className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={sendMessage}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Отправить
                </button>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              Выберите диалог
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

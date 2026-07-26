"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import { apiFetch, getStoredUser } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const user = getStoredUser();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const connectWs = useCallback((dialogId: number) => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setConnected(false);
    }

    const token = localStorage.getItem("token");
    if (!token) return;

    const ws = new WebSocket(
      `${API.replace("http", "ws")}/api/v1/chat/ws/${dialogId}?token=${token}`
    );

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "message") {
          setMessages((prev) => {
            if (prev.some((m) => m.id === msg.id)) return prev;
            return [...prev, msg];
          });
        }
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
    };

    ws.onerror = () => {
      setConnected(false);
    };

    wsRef.current = ws;
  }, []);

  const loadMessages = async (dialogId: number) => {
    setSelectedDialog(dialogId);
    try {
      const data = await apiFetch(`/api/v1/chat/dialogs/${dialogId}/messages`);
      setMessages(data);
      connectWs(dialogId);
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedDialog) return;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text: newMessage }));
      setNewMessage("");
    } else {
      try {
        await apiFetch("/api/v1/chat/messages", {
          method: "POST",
          body: JSON.stringify({ dialog_id: selectedDialog, text: newMessage }),
        });
        setNewMessage("");
      } catch (err: any) {
        alert(err.message);
      }
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

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
              <div className="border-b px-4 py-2 flex items-center gap-2">
                <span className="text-sm font-medium">Диалог #{selectedDialog}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    connected ? "bg-green-500" : "bg-gray-400"
                  }`}
                />
                <span className="text-xs text-gray-400">
                  {connected ? "Онлайн" : "Оффлайн"}
                </span>
              </div>
              <div className="flex-1 overflow-auto p-4 space-y-3">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`max-w-md ${
                      msg.sender_id === user?.id ? "ml-auto" : ""
                    }`}
                  >
                    <div
                      className={`rounded-lg px-4 py-2 ${
                        msg.sender_id === user?.id
                          ? "bg-blue-100"
                          : "bg-gray-100"
                      }`}
                    >
                      <p className="text-sm">{msg.text}</p>
                    </div>
                    <p
                      className={`text-xs text-gray-400 mt-1 ${
                        msg.sender_id === user?.id ? "text-right" : ""
                      }`}
                    >
                      {new Date(msg.created_at).toLocaleTimeString("ru-RU")}
                    </p>
                  </div>
                ))}
                <div ref={messagesEndRef} />
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

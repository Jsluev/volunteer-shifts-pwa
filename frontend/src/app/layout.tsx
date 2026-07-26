import type { Metadata, Viewport } from "next";
import "./globals.css";
import ServiceWorker from "./sw-register";
import { Toaster } from "@/components/Toast";

export const metadata: Metadata = {
  title: "Volunteer Shifts",
  description: "Управление сменами волонтёров в больницах",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <ServiceWorker />
        <Toaster />
        {children}
      </body>
    </html>
  );
}

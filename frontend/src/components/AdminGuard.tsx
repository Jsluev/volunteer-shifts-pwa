"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getStoredUser } from "@/lib/api";

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    const user = getStoredUser();
    if (!user || !["coordinator", "admin", "controller"].includes(user.role)) {
      router.replace("/schedule");
      return;
    }
    setAllowed(true);
  }, [router]);

  if (!allowed) return null;
  return <>{children}</>;
}

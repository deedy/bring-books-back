"use client";

import { useEffect } from "react";
import { registerSW } from "@/lib/offline";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

export default function SWRegister() {
  useEffect(() => {
    if (OFFLINE_ENABLED) registerSW();
  }, []);
  return null;
}
